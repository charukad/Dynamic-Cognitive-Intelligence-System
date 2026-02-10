"""
Chat API Router

Exposes endpoints for real-time chat with the AI.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import StreamingResponse

from src.services.chat.service import chat_service
from src.core import get_logger

router = APIRouter(tags=["chat"])
logger = get_logger(__name__)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    system_prompt: Optional[str] = "You are DCIS, an advanced AI orchestration system."
    stream: bool = False

@router.post("/chat/completions")
async def chat_completions(request: ChatRequest):
    """
    Standard chat completion endpoint.
    Supports streaming via Server-Sent Events (SSE) if stream=True.
    """
    # Create message history list
    history = [{"role": m.role, "content": m.content} for m in request.messages]
    
    if request.stream:
        return StreamingResponse(
            stream_generator(history, request.system_prompt),
            media_type="text/event-stream"
        )
    else:
        try:
            response = await chat_service.chat_completion(
                messages=history,
                system_prompt=request.system_prompt
            )
            return {"role": "assistant", "content": response}
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

async def stream_generator(messages, system_prompt):
    """Generate SSE events for streaming."""
    try:
        async for chunk in chat_service.chat_stream(messages, system_prompt):
            # Format as OpenAI-compatible SSE
            data = {"choices": [{"delta": {"content": chunk}}]}
            yield f"data: {json.dumps(data)}\n\n"
            
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Stream error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
