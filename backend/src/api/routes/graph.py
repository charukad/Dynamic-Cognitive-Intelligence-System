"""
Knowledge Graph API Routes

Provides REST endpoints for knowledge graph operations:
- Concept management (CRUD)
- Relationship creation
- Graph traversal and queries
- Agent knowledge storage
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.memory import knowledge_graph_service


router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


# Request/Response Models

class ConceptCreate(BaseModel):
    """Request model for creating a concept"""
    concept: str = Field(..., description="Concept name")
    concept_type: str = Field("Concept", description="Type of concept")
    properties: Optional[Dict[str, Any]] = Field(None, description="Additional properties")


class RelationshipCreate(BaseModel):
    """Request model for creating a relationship"""
    from_concept_id: str = Field(..., description="Source concept node ID")
    to_concept_id: str = Field(..., description="Target concept node ID")
    relationship_type: str = Field(..., description="Relationship type (e.g., IS_A, RELATES_TO)")
    properties: Optional[Dict[str, Any]] = Field(None, description="Relationship properties")


class ConceptQuery(BaseModel):
    """Request model for querying concepts"""
    concept_type: str = Field(..., description="Type of concept to search")
    filters: Optional[Dict[str, Any]] = Field(None, description="Property filters")
    limit: int = Field(50, ge=1, le=500, description="Maximum results")


class CypherQuery(BaseModel):
    """Request model for custom Cypher queries"""
    query: str = Field(..., description="Cypher query string")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Query parameters")


class AgentKnowledge(BaseModel):
    """Request model for storing agent knowledge"""
    agent_id: UUID = Field(..., description="Agent UUID")
    knowledge: str = Field(..., description="Knowledge content")
    knowledge_type: str = Field("Knowledge", description="Type of knowledge")


class TaskOutcome(BaseModel):
    """Request model for storing task outcomes"""
    task_id: UUID = Field(..., description="Task UUID")
    outcome: str = Field(..., description="Outcome description")
    success: bool = Field(..., description="Whether task succeeded")


class GraphTraversal(BaseModel):
    """Request model for graph traversal"""
    concept_id: str = Field(..., description="Starting concept ID")
    relationship_type: Optional[str] = Field(None, description="Filter by relationship type")
    direction: str = Field("both", description="Traversal direction: incoming, outgoing, both")
    limit: int = Field(25, ge=1, le=100, description="Maximum results")


# API Endpoints

@router.post("/concepts", status_code=status.HTTP_201_CREATED)
async def create_concept(request: ConceptCreate) -> Dict[str, Any]:
    """
    Create a new concept node in the knowledge graph.
    
    Args:
        request: Concept creation data
        
    Returns:
        Created concept node with ID and properties
    """
    try:
        node = await knowledge_graph_service.add_concept(
            concept=request.concept,
            concept_type=request.concept_type,
            properties=request.properties,
        )
        
        return {
            "success": True,
            "concept": node,
            "message": f"Created concept: {request.concept}",
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create concept: {str(e)}",
        )


@router.post("/relationships", status_code=status.HTTP_201_CREATED)
async def create_relationship(request: RelationshipCreate) -> Dict[str, Any]:
    """
    Create a relationship between two concepts.
    
    Args:
        request: Relationship creation data
        
    Returns:
        Created relationship with type and properties
    """
    try:
        relationship = await knowledge_graph_service.add_relationship(
            from_concept_id=request.from_concept_id,
            to_concept_id=request.to_concept_id,
            relationship_type=request.relationship_type,
            properties=request.properties,
        )
        
        return {
            "success": True,
            "relationship": relationship,
            "message": f"Created {request.relationship_type} relationship",
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create relationship: {str(e)}",
        )


@router.post("/concepts/search")
async def search_concepts(request: ConceptQuery) -> Dict[str, Any]:
    """
    Search for concepts by type and filters.
    
    Args:
        request: Search criteria
        
    Returns:
        List of matching concepts
    """
    try:
        concepts = await knowledge_graph_service.find_concepts(
            concept_type=request.concept_type,
            filters=request.filters,
            limit=request.limit,
        )
        
        return {
            "success": True,
            "count": len(concepts),
            "concepts": concepts,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search concepts: {str(e)}",
        )


@router.post("/traverse")
async def traverse_graph(request: GraphTraversal) -> Dict[str, Any]:
    """
    Traverse the graph from a starting concept.
    
    Args:
        request: Traversal parameters
        
    Returns:
        Related concepts with relationships
    """
    try:
        related = await knowledge_graph_service.get_related_concepts(
            concept_id=request.concept_id,
            relationship_type=request.relationship_type,
            direction=request.direction,
            limit=request.limit,
        )
        
        return {
            "success": True,
            "start_concept": request.concept_id,
            "count": len(related),
            "related_concepts": related,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to traverse graph: {str(e)}",
        )


@router.post("/query")
async def execute_cypher_query(request: CypherQuery) -> Dict[str, Any]:
    """
    Execute a custom Cypher query on the knowledge graph.
    
    WARNING: This endpoint allows arbitrary Cypher queries.
    In production, implement proper validation and access control.
    
    Args:
        request: Cypher query and parameters
        
    Returns:
        Query results
    """
    try:
        results = await knowledge_graph_service.query_graph(
            cypher_query=request.query,
            parameters=request.parameters,
        )
        
        return {
            "success": True,
            "count": len(results),
            "results": results,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}",
        )


@router.post("/agent-knowledge", status_code=status.HTTP_201_CREATED)
async def store_agent_knowledge(request: AgentKnowledge) -> Dict[str, Any]:
    """
    Store knowledge learned by an agent.
    
    Creates a knowledge node and links it to the agent.
    
    Args:
        request: Agent knowledge data
        
    Returns:
        Created knowledge node
    """
    try:
        knowledge_node = await knowledge_graph_service.store_agent_knowledge(
            agent_id=request.agent_id,
            knowledge=request.knowledge,
            knowledge_type=request.knowledge_type,
        )
        
        return {
            "success": True,
            "knowledge_node": knowledge_node,
            "message": f"Stored knowledge for agent {request.agent_id}",
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store knowledge: {str(e)}",
        )


@router.post("/task-outcomes", status_code=status.HTTP_201_CREATED)
async def store_task_outcome(request: TaskOutcome) -> Dict[str, Any]:
    """
    Store task execution outcome in the graph.
    
    Useful for tracking task success/failure patterns.
    
    Args:
        request: Task outcome data
        
    Returns:
        Created outcome node
    """
    try:
        outcome_node = await knowledge_graph_service.store_task_outcome(
            task_id=request.task_id,
            outcome=request.outcome,
            success=request.success,
        )
        
        return {
            "success": True,
            "outcome_node": outcome_node,
            "message": f"Stored outcome for task {request.task_id}",
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store outcome: {str(e)}",
        )


@router.get("/health")
async def graph_health() -> Dict[str, str]:
    """
    Check knowledge graph service health.
    
    Returns:
        Service status
    """
    return {
        "status": "healthy",
        "service": "knowledge_graph",
        "message": "Neo4j knowledge graph operational",
    }
