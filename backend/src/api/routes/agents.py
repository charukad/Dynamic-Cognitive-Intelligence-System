"""Agent API endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.domain.models import Agent, AgentStatus, AgentType
from src.infrastructure.repositories import agent_repository
from src.schemas import AgentCreate, AgentResponse, AgentUpdate
# socket_manager removed - using native FastAPI WebSocket

router = APIRouter(prefix="/agents", tags=["agents"])

# Metrics schema
from src.schemas.metrics import MetricsResponse, AgentMetrics
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any
import json
import random

@router.get("/metrics", response_model=MetricsResponse)
async def get_agent_metrics():
    """Get aggregated metrics for all agents."""
    from src.services.monitoring.metrics import metrics_collector
    
    agents = await agent_repository.list()
    metrics = []
    
    for agent in agents:
        # Get real metrics from collector and metadata
        latency_stats = metrics_collector.get_histogram_stats(
            "agent_response_time", 
            tags={"agent_id": str(agent.id)}
        )
        
        metrics.append(AgentMetrics(
            agent_id=str(agent.id),
            name=agent.name,
            total_tasks=agent.metadata.get('total_tasks', 0),
            success_rate=agent.metadata.get('success_rate', 0.0),
            avg_response_time=latency_stats.get('avg', 0.0),
            elo_rating=agent.metadata.get('elo_rating', 1200),
            dream_cycles=agent.metadata.get('dream_cycles', 0),
            insights_generated=agent.metadata.get('insights_generated', 0),
            matches_won=agent.metadata.get('matches_won', 0),
            matches_lost=agent.metadata.get('matches_lost', 0)
        ))
    
    return MetricsResponse(agents=metrics)

@router.websocket("/metrics")
async def websocket_metrics(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent metrics.
    """
    from src.services.monitoring.metrics import metrics_collector
    
    await websocket.accept()
    try:
        while True:
            # Send metrics every 5 seconds
            # In a real implementation, this would subscribe to an event bus
            agents = await agent_repository.list()
            metrics = []
            
            for agent in agents:
                latency_stats = metrics_collector.get_histogram_stats(
                    "agent_response_time", 
                    tags={"agent_id": str(agent.id)}
                )
                
                metrics.append(AgentMetrics(
                    agent_id=str(agent.id),
                    name=agent.name,
                    total_tasks=agent.metadata.get('total_tasks', 0),
                    success_rate=agent.metadata.get('success_rate', 0.0),
                    avg_response_time=latency_stats.get('avg', 0.0),
                    elo_rating=agent.metadata.get('elo_rating', 1200),
                    dream_cycles=agent.metadata.get('dream_cycles', 0),
                    insights_generated=agent.metadata.get('insights_generated', 0),
                    matches_won=agent.metadata.get('matches_won', 0),
                    matches_lost=agent.metadata.get('matches_lost', 0)
                ).model_dump())
            
            await websocket.send_json({"agents": metrics})
            
            import asyncio
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        pass



@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(agent_data: AgentCreate) -> AgentResponse:
    """
    Create a new agent.

    Args:
        agent_data: Agent creation data

    Returns:
        Created agent

    Raises:
        HTTPException: If validation fails
    """
    try:
        agent_type = AgentType(agent_data.agent_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid agent_type. Must be one of: {[t.value for t in AgentType]}",
        )

    agent = Agent(
        name=agent_data.name,
        agent_type=agent_type,
        temperature=agent_data.temperature,
        system_prompt=agent_data.system_prompt,
        model_name=agent_data.model_name,
        metadata=agent_data.metadata,
    )

    created_agent = await agent_repository.create(agent)
    
    # TODO: Broadcast via WebSocket ConnectionManager if needed
    # await connection_manager.broadcast_agent_status(...)
    
    return AgentResponse.model_validate(created_agent)


@router.get("/", response_model=List[AgentResponse])
async def list_agents(skip: int = 0, limit: int = 100) -> List[AgentResponse]:
    """
    List all agents with pagination.

    Args:
        skip: Number of items to skip
        limit: Maximum number of items to return

    Returns:
        List of agents
    """
    agents = await agent_repository.list(skip=skip, limit=limit)
    return [AgentResponse.model_validate(agent) for agent in agents]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: UUID) -> AgentResponse:
    """
    Get agent by ID.

    Args:
        agent_id: Agent UUID

    Returns:
        Agent details

    Raises:
        HTTPException: If agent not found
    """
    agent = await agent_repository.get_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )
    return AgentResponse.model_validate(agent)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: UUID, agent_data: AgentUpdate) -> AgentResponse:
    """
    Update agent.

    Args:
        agent_id: Agent UUID
        agent_data: Update data

    Returns:
        Updated agent

    Raises:
        HTTPException: If agent not found or validation fails
    """
    agent = await agent_repository.get_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    # Update fields
    if agent_data.name is not None:
        agent.name = agent_data.name
    if agent_data.temperature is not None:
        agent.temperature = agent_data.temperature
    if agent_data.system_prompt is not None:
        agent.system_prompt = agent_data.system_prompt
    if agent_data.model_name is not None:
        agent.model_name = agent_data.model_name
    if agent_data.status is not None:
        try:
            agent.status = AgentStatus(agent_data.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {[s.value for s in AgentStatus]}",
            )
    if agent_data.metadata is not None:
        agent.metadata.update(agent_data.metadata)

    updated_agent = await agent_repository.update(agent)
    return AgentResponse.model_validate(updated_agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: UUID) -> None:
    """
    Delete agent.

    Args:
        agent_id: Agent UUID

    Raises:
        HTTPException: If agent not found
    """
    deleted = await agent_repository.delete(agent_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )


@router.get("/type/{agent_type}", response_model=List[AgentResponse])
async def get_agents_by_type(agent_type: str) -> List[AgentResponse]:
    """
    Get agents by type.

    Args:
        agent_type: Agent type

    Returns:
        List of agents of the specified type
    """
    agents = await agent_repository.get_by_type(agent_type)
    return [AgentResponse.model_validate(agent) for agent in agents]


@router.get("/status/available", response_model=List[AgentResponse])
async def get_available_agents() -> List[AgentResponse]:
    """
    Get all available (idle) agents.

    Returns:
        List of available agents
    """
    agents = await agent_repository.get_available_agents()
    return [AgentResponse.model_validate(agent) for agent in agents]


# ✅ NEW: Search agents by capability
@router.get("/search/capability/{capability}", response_model=List[AgentResponse])
async def search_agents_by_capability(capability: str) -> List[AgentResponse]:
    """
    Search agents by capability.
    
    Args:
        capability: Capability to search for (e.g., "data_analysis", "code_generation")
    
    Returns:
        List of agents with the specified capability
    
    Example:
        GET /agents/search/capability/data_analysis
    """
    agents = await agent_repository.search_by_capability(capability)
    return [AgentResponse.model_validate(agent) for agent in agents]
