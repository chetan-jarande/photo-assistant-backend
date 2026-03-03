from typing import List, Annotated, Literal
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI

from tools.generative_tools import (
    generate_new_image,
    auto_enhance_image,
    remove_background,
)

CREATIVE_STUDIO_TOOLS = [generate_new_image, auto_enhance_image, remove_background]

CREATIVE_STUDIO_SYSTEM_PROMPT = """You are the Creative Studio Agent, an artistic sub-agent responsible for generating, enhancing, and modifying images.
Your primary role is to use generative AI models to create new visuals or improve existing ones.

You have access to the following tools:
- `generate_new_image`: Create new images from text prompts and styles.
- `auto_enhance_image`: Automatically improve photo quality (color, exposure).
- `remove_background`: Isolate the subject by removing the background.

When receiving a request:
1. Identify the creative intent (generation vs. modification).
2. If modification is requested, ensure you have the `image_id`.
3. If generation is requested, extract a detailed prompt and style.
4. Execute the tool and return the result (e.g., URL of the new image).

Do not perform any metadata or search operations; focus strictly on image creation and manipulation.
"""


def create_creative_studio_agent(llm: ChatGoogleGenerativeAI):
    """
    Creates the Creative Studio agent graph.
    """
    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(CREATIVE_STUDIO_TOOLS)

    # Define the prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", CREATIVE_STUDIO_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    # Define the agent node
    async def creative_studio_node(state: dict, config: RunnableConfig):
        messages = state.get("messages", [])
        chain = prompt | llm_with_tools
        result = await chain.ainvoke({"messages": messages}, config)
        return {"messages": [result]}

    # Define the graph
    workflow = StateGraph(dict)  # Using a simple dict state for now

    workflow.add_node("agent", creative_studio_node)
    workflow.add_node("tools", ToolNode(CREATIVE_STUDIO_TOOLS))

    workflow.set_entry_point("agent")

    # Conditional edge to route to tools or end
    def should_continue(state: dict) -> Literal["tools", "__end__"]:
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return "__end__"

    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")

    return workflow.compile()
