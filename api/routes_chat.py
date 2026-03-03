from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import logging

from langchain_core.messages import HumanMessage
from agents.orchestrator import create_orchestrator

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize the orchestrator graph
# We initialize it once. Checkpointer is stateless (connection based).
orchestrator_graph = create_orchestrator()


class ChatRequest(BaseModel):
    session_id: str
    message: str
    attachments: Optional[List[Dict[str, Any]]] = None


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response using Server-Sent Events (SSE).
    """
    session_id = request.session_id
    user_message = request.message

    # Construct the input state
    inputs = {"messages": [HumanMessage(content=user_message)]}

    # Config for the graph run
    config = {"configurable": {"thread_id": session_id}}

    async def event_generator():
        try:
            # Stream events from the graph
            # We use astream to get updates from nodes as they complete
            # Or astream_events for more granular updates (tokens)
            # For simplicity and structure, let's use astream first to see node transitions

            # Using astream_events to get tokens and tool calls would be ideal for a rich UI
            # But let's start with node updates for the backend prototype

            async for event in orchestrator_graph.astream(inputs, config=config):
                # event is a dict of node_name: state_update
                for node, values in event.items():
                    # Check if we have a message from the agent
                    if "messages" in values:
                        last_message = values["messages"][-1]

                        if isinstance(last_message, dict):
                            # Should be a BaseMessage, but let's be safe
                            content = last_message.get("content", "")
                            msg_type = "unknown"
                        else:
                            content = last_message.content
                            msg_type = last_message.type

                        # Prepare payload
                        payload = {
                            "node": node,
                            "type": msg_type,
                            "content": content,
                            "tool_calls": getattr(last_message, "tool_calls", []),
                        }

                        yield f"data: {json.dumps(payload, default=str)}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            error_payload = {"error": str(e)}
            yield f"data: {json.dumps(error_payload, default=str)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Standard REST endpoint for chat (non-streaming).
    """
    session_id = request.session_id
    user_message = request.message

    inputs = {"messages": [HumanMessage(content=user_message)]}
    config = {"configurable": {"thread_id": session_id}}

    try:
        final_state = await orchestrator_graph.ainvoke(inputs, config=config)
        messages = final_state["messages"]
        last_message = messages[-1]

        return {
            "session_id": session_id,
            "response": last_message.content,
            "tool_calls": getattr(last_message, "tool_calls", []),
        }
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
