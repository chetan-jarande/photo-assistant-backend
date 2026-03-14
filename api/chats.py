from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from enum import Enum
import asyncio
import json

chat_router = APIRouter(prefix="/chat", tags=["Chat"])


class RoleEnum(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Attachment(BaseModel):
    id: str = Field(
        ...,
        title="Attachment ID",
        description="Unique identifier for the attachment",
        examples=["att-456"],
    )
    url: str = Field(
        ...,
        title="Attachment URL",
        description="URL to the attachment resource",
        examples=["https://example.com/file.pdf"],
    )
    name: str = Field(
        ...,
        title="Attachment Name",
        description="Display name of the attachment",
        examples=["document.pdf"],
    )


class ComponentPayload(BaseModel):
    type: str = Field(
        ...,
        title="Component Type",
        description="Type of the UI component to render",
        examples=["DuplicateResolver"],
    )
    data: Dict[str, Any] = Field(
        ...,
        title="Component Data",
        description="Data payload for the component",
        examples=[{"group_id": "dup_123"}],
    )


class Message(BaseModel):
    id: str = Field(
        ...,
        title="Message ID",
        description="Unique identifier for the message",
        examples=["msg-789"],
    )
    role: RoleEnum = Field(
        ...,
        title="Role",
        description="Role of the sender",
        examples=[RoleEnum.USER],
    )
    content: str = Field(
        ...,
        title="Content",
        description="Text content of the message",
        examples=["Hello, world!"],
    )
    componentPayload: Optional[ComponentPayload] = Field(
        default=None,
        title="Component Payload",
        description="Optional component data for rendering rich UI elements",
    )


class ChatRequest(BaseModel):
    session_id: str = Field(
        ...,
        title="Session ID",
        description="Unique identifier for the chat session",
        examples=["sess-abc-123"],
    )
    message: str = Field(
        ...,
        title="Message",
        description="The text message from the user",
        examples=["Find duplicate images"],
    )
    attachments: Optional[List[Attachment]] = Field(
        default_factory=list,
        title="Attachments",
        description="List of file attachments included with the message",
    )
    history: Optional[List[Message]] = Field(
        default_factory=list,
        title="History",
        description="Previous messages in the chat session",
    )


@chat_router.post(
    "/stream",
    response_class=StreamingResponse,
    summary="Stream Chat Events",
    description="Streaming chat endpoint using Server-Sent Events (SSE) for real-time text and component rendering updates.",
    responses={
        200: {
            "description": "SSE stream yielding JSON events.",
            "content": {"text/event-stream": {}},
        }
    },
)
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).
    """

    async def event_generator():
        msg_lower = request.message.lower()

        reasoning_steps = [
            "🧠 Orchestrator analyzing intent...",
            "🔍 Checking gallery context...",
        ]

        if "duplicate" in msg_lower:
            reasoning_steps.extend(
                ["⚙️ Asset Manager scanning image hashes...", "✅ Potential matches found. Synthesizing..."]
            )
        elif "generate" in msg_lower:
            reasoning_steps.extend(["🎨 Creative Studio initializing models...", "✨ Rendering requested imagery..."])
        else:
            reasoning_steps.append("📝 Formulating response...")

        for step in reasoning_steps:
            yield f"data: {json.dumps({'status': step})}\n\n"
            await asyncio.sleep(0.5)

        yield f"data: {json.dumps({'status': None})}\n\n"

        if "duplicate" in msg_lower:
            intro = "<p>I found a potential duplicate set in your recent uploads. Please review them below:</p>"
            for i in range(len(intro)):
                yield f"data: {json.dumps({'text': intro[i]})}\n\n"
                await asyncio.sleep(0.01)

            yield f"data: {json.dumps({'component': {'type': 'DuplicateResolver', 'data': {'group_id': 'dup_group_01', 'images': [{'id': 'img_001', 'url': 'https://images.unsplash.com/photo-1516822264585-ea0a03bb1f70?q=80&w=300&auto=format&fit=crop', 'size': '4.2 MB', 'res': '4000x3000'}, {'id': 'img_002', 'url': 'https://images.unsplash.com/photo-1516822264585-ea0a03bb1f70?q=80&w=300&auto=format&fit=crop&q=50', 'size': '1.1 MB', 'res': '2000x1500', 'note': 'Lower Res'}]}}})}\n\n"
        else:
            reply = f"<p>Based on our chat history, here is your simulated response to: {request.message}</p>"
            if request.attachments:
                reply += f"<p>I successfully received <strong>{len(request.attachments)} attachment(s)</strong>.</p>"

            chunks = [reply[i : i + 5] for i in range(0, len(reply), 5)]
            for chunk in chunks:
                yield f"data: {json.dumps({'text': chunk})}\n\n"
                await asyncio.sleep(0.05)

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


class ChatResponse(BaseModel):
    reply: str = Field(
        ...,
        title="Reply",
        description="The plain text response from the REST endpoint",
        examples=["This is a standard REST response. Please use /chat/stream for SSE."],
    )


@chat_router.post(
    "/",
    response_model=ChatResponse,
    summary="Standard Chat (REST)",
    description="Standard REST endpoint for chat interactions that do not require streaming.",
)
async def chat_rest(request: ChatRequest):
    """
    Standard REST endpoint for chat.
    """
    return ChatResponse(reply="This is a standard REST response. Please use /chat/stream for SSE.")
