"""
Advanced Memory Visualization API endpoints.

Provides graph data formatted for frontend visualization libraries.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.memory import knowledge_graph_service, episodic_memory_service

router = APIRouter(prefix="/memory/visualization", tags=["memory-visualization"])


# ============================================================================
# Response Models
# ============================================================================

class GraphNodeResponse(BaseModel):
    """Node in knowledge graph."""
    
    id: str
    label: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    importance: float = 0.5


class GraphEdgeResponse(BaseModel):
    """Edge in knowledge graph."""
    
    source: str
    target: str
    relationship: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphResponse(BaseModel):
    """Complete knowledge graph for visualization."""
    
    nodes: List[GraphNodeResponse]
    edges: List[GraphEdgeResponse]
    stats: Dict[str, int]


class EpisodicTimelineEvent(BaseModel):
    """Event in episodic memory timeline."""
    
    id: str
    timestamp: str
    content: str
    session_id: Optional[str]
    importance: float
    tags: List[str] = Field(default_factory=list)


class MemoryStatsResponse(BaseModel):
    """Memory system statistics."""
    
    total_memories: int
    episodic_count: int
    semantic_count: int
    graph_nodes: int
    graph_relationships: int
    avg_importance: float


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/graph", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph(
    agent_id: Optional[str] = None,
    limit: int = 50,
    concept_type: Optional[str] = None
) -> KnowledgeGraphResponse:
    """
    Get knowledge graph data for visualization.
    
    Args:
        agent_id: Filter by specific agent
        limit: Maximum nodes to return
        concept_type: Filter by concept type
        
    Returns:
        Graph nodes and edges in visualization format
    """
    try:
        nodes = []
        edges = []
        stats = {"total_nodes": 0, "total_edges": 0, "concept_types": 0}

        # Build Cypher query
        # Basic query to get nodes and connected edges
        # We limit the number of paths returned
        where_clause = ""
        params = {"limit": limit}
        
        if agent_id:
            where_clause = "WHERE n.agent_id = $agent_id OR m.agent_id = $agent_id"
            params["agent_id"] = agent_id
        
        if concept_type:
            prefix = "AND" if where_clause else "WHERE"
            where_clause += f" {prefix} (n:{concept_type} OR m:{concept_type})"

        query = f"""
            MATCH (n)-[r]-(m)
            {where_clause}
            RETURN n, r, m
            LIMIT $limit
        """
        
        results = await knowledge_graph_service.query_graph(query, params)
        
        # Process results
        # Neo4j results format depends on the client, assuming list of records
        # where each record is a dict-like object
        
        seen_nodes = set()
        seen_edges = set()
        
        for record in results:
            # Helper to process node
            def process_node(node_data):
                # node_data might be a Node object or dict
                # Adjust based on your actual neo4j_client implementation
                node_id = str(node_data.element_id) if hasattr(node_data, 'element_id') else str(node_data.get('id', ''))
                if not node_id: 
                    # Fallback to creating an ID or using some property
                    node_id = str(node_data.get('elementId', 'unknown'))
                
                if node_id in seen_nodes:
                    return
                seen_nodes.add(node_id)
                
                labels = list(node_data.labels) if hasattr(node_data, 'labels') else node_data.get('labels', [])
                label = labels[0] if labels else "Unknown"
                
                # Try to find a display label property
                display_label = node_data.get('name') or node_data.get('label') or label
                
                nodes.append(GraphNodeResponse(
                    id=node_id,
                    label=display_label,
                    type=label,
                    properties=dict(node_data.items()) if hasattr(node_data, 'items') else dict(node_data),
                    importance=node_data.get('importance', 0.5)
                ))

            # Helper to process edge
            def process_edge(rel_data, start_id, end_id):
                rel_id = str(rel_data.element_id) if hasattr(rel_data, 'element_id') else str(rel_data.get('id', ''))
                if rel_id in seen_edges:
                    return
                seen_edges.add(rel_id)
                
                rel_type = rel_data.type if hasattr(rel_data, 'type') else rel_data.get('type', 'RELATED')
                
                edges.append(GraphEdgeResponse(
                    source=start_id,
                    target=end_id,
                    relationship=rel_type,
                    properties=dict(rel_data.items()) if hasattr(rel_data, 'items') else dict(rel_data)
                ))

            n = record.get('n')
            m = record.get('m')
            r = record.get('r')
            
            if n: process_node(n)
            if m: process_node(m)
            
            if n and m and r:
                n_id = str(n.element_id) if hasattr(n, 'element_id') else str(n.get('id'))
                m_id = str(m.element_id) if hasattr(m, 'element_id') else str(m.get('id'))
                process_edge(r, n_id, m_id)

        stats["total_nodes"] = len(nodes)
        stats["total_edges"] = len(edges)
        
        return KnowledgeGraphResponse(
            nodes=nodes,
            edges=edges,
            stats=stats
        )
        
    except Exception as e:
        # In case of Neo4j failure or empty, return empty graph instead of crashing
        # But log error
        import logging
        logging.getLogger(__name__).error(f"Graph query failed: {e}")
        return KnowledgeGraphResponse(nodes=[], edges=[], stats={"error": 1})


@router.get("/timeline", response_model=List[EpisodicTimelineEvent])
async def get_episodic_timeline(
    agent_id: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 100
) -> List[EpisodicTimelineEvent]:
    """
    Get episodic memory timeline.
    
    Args:
        agent_id: Filter by agent
        session_id: Filter by session
        limit: Maximum events
        
    Returns:
        Chronological list of memory events
    """
    try:
        from src.infrastructure.repositories import memory_repository
        from src.domain.models import MemoryType
        
        memories = []
        if session_id:
            memories = await memory_repository.get_by_session(session_id)
        elif agent_id:
            memories = await memory_repository.get_by_agent(agent_id)
        else:
            # Fallback to recent list if no filters (might be heavy in prod, but ok for dev)
            memories = await memory_repository.list(limit=200)

        # Filter for Episodic only
        episodic_memories = [m for m in memories if m.memory_type == MemoryType.EPISODIC]
        
        # Sort by creation time descending (newest first)
        episodic_memories.sort(key=lambda m: m.created_at, reverse=True)
        episodic_memories = episodic_memories[:limit]
        
        events = []
        for mem in episodic_memories:
            events.append(EpisodicTimelineEvent(
                id=str(mem.id),
                timestamp=mem.created_at.isoformat(),
                content=mem.content,
                session_id=mem.session_id,
                importance=mem.importance_score,
                tags=mem.tags
            ))
            
        return events
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch timeline: {str(e)}"
        )


@router.get("/stats", response_model=MemoryStatsResponse)
async def get_memory_stats(agent_id: Optional[str] = None) -> MemoryStatsResponse:
    """
    Get memory system statistics.
    
    Args:
        agent_id: Filter by specific agent
        
    Returns:
        Comprehensive memory statistics
    """
    try:
        from src.infrastructure.repositories import memory_repository
        from src.domain.models import MemoryType
        
        if agent_id:
            memories = await memory_repository.get_by_agent(agent_id)
        else:
            memories = await memory_repository.list(limit=5000) # Cap for safety
        
        total = len(memories)
        episodic = sum(1 for m in memories if m.memory_type == MemoryType.EPISODIC)
        semantic = sum(1 for m in memories if m.memory_type == MemoryType.SEMANTIC)
        avg_imp = sum(m.importance_score for m in memories) / total if total > 0 else 0.0
        
        # Graph stats (basic count via query)
        graph_nodes = 0
        graph_rels = 0
        try:
             # Fast counts from Neo4j
             # Note: This might be slow if huge graph, but count store usage is fast
             stats = await knowledge_graph_service.query_graph("MATCH (n) RETURN count(n) as count")
             if stats: graph_nodes = stats[0].get('count', 0)
             
             stats_r = await knowledge_graph_service.query_graph("MATCH ()-[r]->() RETURN count(r) as count")
             if stats_r: graph_rels = stats_r[0].get('count', 0)
        except:
            pass # Ignore graph errors for stats
            
        return MemoryStatsResponse(
            total_memories=total,
            episodic_count=episodic,
            semantic_count=semantic,
            graph_nodes=graph_nodes,
            graph_relationships=graph_rels,
            avg_importance=avg_imp
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stats: {str(e)}"
        )
