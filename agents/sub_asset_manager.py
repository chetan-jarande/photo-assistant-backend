from typing import List, Annotated, Literal
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI

from tools.metadata_tools import search_by_location, filter_by_camera_settings
from tools.vision_tools import (
    find_duplicate_photos,
    search_by_entity,
    find_similar_places,
    semantic_image_search,
)

# Define the tools available to the Asset Manager
ASSET_MANAGER_TOOLS = [
    search_by_location,
    filter_by_camera_settings,
    find_duplicate_photos,
    search_by_entity,
    find_similar_places,
    semantic_image_search,
]

ASSET_MANAGER_SYSTEM_PROMPT = """You are the Asset Manager Agent, a specialist sub-agent responsible for organizing, retrieving, and managing the user's photo gallery.
Your primary role is to interact with the database and vision systems to find photos based on metadata, location, visual content, or similarity.

You have access to the following tools:
- `search_by_location`: Find photos near a specific place.
- `filter_by_camera_settings`: Filter by ISO, aperture, shutter speed, camera model.
- `find_duplicate_photos`: Identify near-identical images to clean up the library.
- `search_by_entity`: Find photos containing specific objects (e.g., "cats", "cars").
- `find_similar_places`: Find photos with similar scenery to a reference image.
- `semantic_image_search`: Find photos based on a natural language description.

When you receive a request, analyze it and use the appropriate tool.
If the request is ambiguous, ask for clarification.
Always return a concise summary of the findings or the result of the operation.
Do not hallucinate photo IDs or content. Use the tool outputs as the source of truth.
"""


def create_asset_manager_agent(llm: ChatGoogleGenerativeAI):
    """
    Creates the Asset Manager agent graph.
    """
    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(ASSET_MANAGER_TOOLS)

    # Define the prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", ASSET_MANAGER_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    # Define the agent node
    async def asset_manager_node(state: dict, config: RunnableConfig):
        messages = state.get("messages", [])
        chain = prompt | llm_with_tools
        result = await chain.ainvoke({"messages": messages}, config)
        return {"messages": [result]}

    # Define the graph
    workflow = StateGraph(
        dict
    )  # Using a simple dict state for now, Orchestrator will manage full state

    workflow.add_node("agent", asset_manager_node)
    workflow.add_node("tools", ToolNode(ASSET_MANAGER_TOOLS))

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
