"""Memory API endpoints for search and storage."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.memory import (
    episodic_memory_service,
    knowledge_graph_service,
    semantic_memory_service,
    working_memory_service,
)

router = APIRouter(prefix="/memory", tags=["memory"])


# Request/Response Models

class MemorySearchRequest(BaseModel):
    """Memory search request."""
    
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results")
    min_importance: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum importance filter")


class MemoryStoreRequest(BaseModel):
    """Memory storage request."""
    
    content: str = Field(..., min_length=1, description="Memory content")
    memory_type: str = Field(default="episodic", description="Memory type (episodic, semantic)")
    session_id: Optional[str] = Field(None, description="Session ID for episodic memories")
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Importance score")
    tags: List[str] = Field(default_factory=list, description="Memory tags")


class KnowledgeGraphRequest(BaseModel):
    """Knowledge graph query request."""
    
    concept: Optional[str] = Field(None, description="Concept to search for")
    concept_type: str = Field(default="Concept", description="Type of concept")
    relationship_type: Optional[str] = Field(None, description="Relationship filter")
    limit: int = Field(default=25, ge=1, le=100, description="Maximum results")


class ContextStoreRequest(BaseModel):
    """Working memory context storage request."""
    
    session_id: str = Field(..., description="Session identifier")
    context: dict = Field(..., description="Context data")
    ttl: Optional[int] = Field(None, ge=1, le=86400, description="Time to live in seconds")


# Endpoints

@router.post("/search")
async def search_memories(request: MemorySearchRequest) -> dict:
    """
    Search episodic memories using semantic similarity.
    
    Args:
        request: Search request
        
    Returns:
        Search results
        
    Raises:
        HTTPException: If search fails
    """
    try:
        memories = await episodic_memory_service.retrieve_memories(
            query=request.query,
            limit=request.limit,
            min_importance=request.min_importance,
        )
        
        return {
            "query": request.query,
            "results": [
                {
                    "id": str(m.id),
                    "content": m.content,
                    "importance_score": m.importance_score,
                    "session_id": m.session_id,
                    "tags": m.tags,
                    "created_at": m.created_at.isoformat(),
                }
                for m in memories
            ],
            "count": len(memories),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory search failed: {str(e)}",
        )


@router.get("/sessions")
async def get_recent_sessions(limit: int = 10) -> dict:
    """
    Get recent chat sessions.
    
    Args:
        limit: Maximum number of sessions
        
    Returns:
        List of session IDs
    """
    try:
        sessions = await episodic_memory_service.get_recent_sessions(limit)
        
        return {
            "sessions": sessions,
            "count": len(sessions),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sessions: {str(e)}",
        )


@router.post("/store")
async def store_memory(request: MemoryStoreRequest) -> dict:
    """
    Store a new memory.
    
    Args:
        request: Storage request
        
    Returns:
        Created memory
        
    Raises:
        HTTPException: If storage fails
    """
    try:
        if request.memory_type == "episodic":
            memory = await episodic_memory_service.store_memory(
                content=request.content,
                session_id=request.session_id,
                importance_score=request.importance_score,
                tags=request.tags,
            )
        elif request.memory_type == "semantic":
            memory = await semantic_memory_service.store_knowledge(
                content=request.content,
                tags=request.tags,
                importance_score=request.importance_score,
            )
        else:
            raise ValueError(f"Invalid memory type: {request.memory_type}")
        
        return {
            "id": str(memory.id),
            "memory_type": memory.memory_type.value,
            "content": memory.content,
            "importance_score": memory.importance_score,
            "created_at": memory.created_at.isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory storage failed: {str(e)}",
        )


@router.post("/knowledge/search")
async def search_knowledge(request: MemorySearchRequest) -> dict:
    """
    Search semantic knowledge.
    
    Args:
        request: Search request
        
    Returns:
        Knowledge results
    """
    try:
        knowledge = await semantic_memory_service.retrieve_knowledge(
            query=request.query,
            limit=request.limit,
        )
        
        return {
            "query": request.query,
            "results": [
                {
                    "id": str(k.id),
                    "content": k.content,
                    "importance_score": k.importance_score,
                    "tags": k.tags,
                }
                for k in knowledge
            ],
            "count": len(knowledge),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/graph/query")
async def query_knowledge_graph(request: KnowledgeGraphRequest) -> dict:
    """
    Query knowledge graph.
    
    Args:
        request: Graph query request
        
    Returns:
        Graph query results
    """
    try:
        if request.concept:
            # Find specific concepts
            results = await knowledge_graph_service.find_concepts(
                concept_type=request.concept_type,
                filters={"name": request.concept} if request.concept else None,
                limit=request.limit,
            )
        else:
            # Get all concepts of type
            results = await knowledge_graph_service.find_concepts(
                concept_type=request.concept_type,
                limit=request.limit,
            )
        
        return {
            "concept_type": request.concept_type,
            "results": results,
            "count": len(results),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph query failed: {str(e)}",
        )


@router.post("/context/store")
async def store_context(request: ContextStoreRequest) -> dict:
    """
    Store conversation context in working memory.
    
    Args:
        request: Context storage request
        
    Returns:
        Success status
    """
    try:
        success = await working_memory_service.store_context(
            session_id=request.session_id,
            context=request.context,
            ttl=request.ttl,
        )
        
        return {
            "session_id": request.session_id,
            "stored": success,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/context/{session_id}")
async def get_context(session_id: str) -> dict:
    """
    Retrieve conversation context.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Context data
    """
    try:
        context = await working_memory_service.get_context(session_id)
        
        if context is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No context found for session: {session_id}",
            )
        
        return {
            "session_id": session_id,
            "context": context,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/context/{session_id}")
async def clear_context(session_id: str) -> dict:
    """
    Clear conversation context.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success status
    """
    try:
        success = await working_memory_service.clear_context(session_id)
        
        return {
            "session_id": session_id,
            "cleared": success,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/stats")
async def get_memory_stats() -> Dict[str, Any]:
    """Get memory system statistics."""
    try:
        # Get stats from services
        episodic_stats = await episodic_memory_service.get_stats()
        semantic_stats = await semantic_memory_service.get_stats()
        
        total_memories = episodic_stats.get("total_count", 0) + semantic_stats.get("total_count", 0)
        
        # Calculate weighted average importance
        total_importance = (
            (episodic_stats.get("avg_importance", 0) * episodic_stats.get("total_count", 0)) +
            (semantic_stats.get("avg_importance", 0) * semantic_stats.get("total_count", 0))
        )
        avg_importance = total_importance / total_memories if total_memories > 0 else 0.0
        
        return {
            "semantic_count": semantic_stats.get("total_count", 0),
            "episodic_count": episodic_stats.get("total_count", 0),
            "avg_importance": avg_importance,
            "total_memories": total_memories,
            "distribution": {
                "semantic": semantic_stats.get("total_count", 0),
                "episodic": episodic_stats.get("total_count", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get memory stats: {str(e)}",
        )

