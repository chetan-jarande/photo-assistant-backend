import functools
import operator
from typing import Annotated, Sequence, TypedDict, Union, List
from pydantic import BaseModel, Field

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    FunctionMessage,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from core.config import settings
from agents.sub_asset_manager import create_asset_manager_agent
from agents.sub_creative_studio import create_creative_studio_agent
from database.checkpointer import SurrealDBCheckpointer


# Define the Agent State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str


# Define the Supervisor Prompt
system_prompt = (
    "You are the supervisor of a photography assistant system.\n"
    "Your goal is to orchestrate the actions of two sub-agents: 'AssetManager' and 'CreativeStudio'.\n"
    "1. 'AssetManager': For finding photos, managing metadata, searching by location, duplicates, or entities.\n"
    "2. 'CreativeStudio': For generating new images, editing, enhancing, or removing backgrounds.\n"
    "3. If the user's request is a general question or a greeting, respond directly using 'FINISH'.\n"
    "4. If the sub-agents have completed their work and you have the answer, respond to the user using 'FINISH'.\n"
    "Given the conversation, decide who should act next.\n"
    "Select one of: ['AssetManager', 'CreativeStudio', 'FINISH']"
)

options = ["AssetManager", "CreativeStudio", "FINISH"]


# Function to create the supervisor chain
def create_supervisor_node(llm: ChatGoogleGenerativeAI):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "Given the conversation above, who should act next?"
                " Or should we FINISH? Select one of: {options}",
            ),
        ]
    ).partial(options=str(options), team_members=", ".join(options))

    # Using structured output or function calling for routing
    # Since we are using Gemini, we can use `with_structured_output` if available or simple tool binding
    # For now, let's use a simple routing via tool calling convention or just text classification if simple.
    # The plan mentions "Uses Pydantic structured outputs to guarantee the exact shape".

    from pydantic import BaseModel, Field

    class Router(BaseModel):
        next: str = Field(description="The next agent to act or 'FINISH'")

    router_chain = prompt | llm.with_structured_output(Router)
    return router_chain


async def supervisor_node(state: AgentState, supervisor_chain):
    result = await supervisor_chain.ainvoke(state)
    return {"next": result.next}


def create_orchestrator():
    """
    Builds the main LangGraph orchestrator.
    """
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro", google_api_key=settings.GOOGLE_API_KEY, temperature=0
    )

    # Create sub-agents
    asset_manager_graph = create_asset_manager_agent(llm)
    creative_studio_graph = create_creative_studio_agent(llm)

    # Wrapper for sub-agents to adapt to the state
    async def call_asset_manager(state: AgentState):
        response = await asset_manager_graph.ainvoke({"messages": state["messages"]})
        return {
            "messages": [response["messages"][-1]]
        }  # return the last message from the sub-agent

    async def call_creative_studio(state: AgentState):
        response = await creative_studio_graph.ainvoke({"messages": state["messages"]})
        return {"messages": [response["messages"][-1]]}

    # Create the graph
    workflow = StateGraph(AgentState)

    # Create the supervisor node
    supervisor_chain = create_supervisor_node(llm)
    workflow.add_node(
        "supervisor",
        functools.partial(supervisor_node, supervisor_chain=supervisor_chain),
    )

    # Add sub-agent nodes
    workflow.add_node("AssetManager", call_asset_manager)
    workflow.add_node("CreativeStudio", call_creative_studio)

    # Entry point
    workflow.set_entry_point("supervisor")

    # Routing logic
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        {
            "AssetManager": "AssetManager",
            "CreativeStudio": "CreativeStudio",
            "FINISH": END,
        },
    )

    # Edges from sub-agents back to supervisor
    workflow.add_edge("AssetManager", "supervisor")
    workflow.add_edge("CreativeStudio", "supervisor")

    # Checkpointer
    checkpointer = SurrealDBCheckpointer()

    return workflow.compile(checkpointer=checkpointer)
