"""Query and orchestration API endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query as QueryParam, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.services.orchestrator import meta_orchestrator

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    """Query request schema."""

    query: str = Field(..., min_length=1, description="User query")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    task_type: Optional[str] = Field(None, description="Task type hint (research, coding, creative, analysis)")
    stream: bool = Field(default=False, description="Enable streaming response")


class QueryResponse(BaseModel):
    """Query response schema."""

    task_id: str
    description: str
    status: str
    result: dict


@router.post("/", response_model=QueryResponse)
async def process_query(request: QueryRequest) -> QueryResponse:
    """
    Process a user query using multi-agent orchestration.
    
    Args:
        request: Query request
        
    Returns:
        Query result
        
    Raises:
        HTTPException: If query processing fails
    """
    try:
        result = await meta_orchestrator.process_query(
            query=request.query,
            session_id=request.session_id,
            task_type=request.task_type,
        )
        
        return QueryResponse(
            task_id=result.get("task_id", "unknown"),
            description=request.query,
            status=result.get("status", "completed"),
            result=result,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}",
        )


@router.post("/stream")
async def process_query_stream(request: QueryRequest):
    """
    Process query with streaming updates (Server-Sent Events).
    
    Args:
        request: Query request
        
    Returns:
        Streaming response
    """
    async def event_generator():
        """Generate SSE events."""
        try:
            async for update in meta_orchestrator.process_query_stream(
                query=request.query,
                session_id=request.session_id,
                task_type=request.task_type,
            ):
                # Format as SSE
                import json
                yield f"data: {json.dumps(update)}\n\n"
                
        except Exception as e:
            import json
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/status/{task_id}")
async def get_task_status(task_id: str) -> dict:
    """
    Get task execution status and hierarchy.
    
    Args:
        task_id: Task UUID
        
    Returns:
        Task status and hierarchy
        
    Raises:
        HTTPException: If task not found
    """
    try:
        from uuid import UUID
        task_uuid = UUID(task_id)
        
        status_info = await meta_orchestrator.get_task_status(task_uuid)
        
        if "error" in status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=status_info["error"],
            )
        
        return status_info
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
