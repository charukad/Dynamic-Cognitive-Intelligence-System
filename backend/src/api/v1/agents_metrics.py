"""
Agents Metrics API Endpoints

Provides real-time metrics and performance data for all agents.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List
import asyncio
import logging
from datetime import datetime

from src.services.metrics.aggregator import MetricsAggregator
from src.infrastructure.metrics.redis_repository import get_cache_repository
from src.infrastructure.metrics.postgres_repository import get_metrics_repository

logger = logging.getLogger(__name__)

router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")

manager = ConnectionManager()

# Initialize metrics aggregator (singleton pattern)
_aggregator: MetricsAggregator = None


async def get_aggregator() -> MetricsAggregator:
    """Get or initialize the metrics aggregator"""
    global _aggregator
    if _aggregator is None:
        repository = await get_metrics_repository()
        cache = await get_cache_repository()
        _aggregator = MetricsAggregator(repository, cache)
    return _aggregator


async def get_agent_metrics_data() -> Dict[str, Any]:
    """Get REAL metrics from aggregator (not mock data)"""
    try:
        aggregator = await get_aggregator()
        agents = await aggregator.get_all_agents_metrics()
        
        return {
            "agents": agents,
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(agents),
        }
    except Exception as e:
        logger.error(f"Failed to get agent metrics: {e}", exc_info=True)
        # Return minimal data on error
        return {
            "agents": [],
            "timestamp": datetime.now().isoformat(),
            "total_agents": 0,
            "error": str(e)
        }


@router.get("/v1/agents/metrics")
async def get_agents_metrics() -> Dict[str, Any]:
    """
    Get current metrics for all agents.
    
    Returns real-time performance metrics including:
    - Task completion statistics
    - Success rates
    - Response times
    - ELO ratings
    - Dream cycles and insights
    - Tournament match records
    
    **This now returns REAL data from Redis and PostgreSQL, not mocks.**
    """
    return await get_agent_metrics_data()


@router.websocket("/v1/agents/metrics")
async def websocket_agents_metrics(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent metrics updates.
    
    Sends updated metrics every 5 seconds to connected clients.
    **Now streams REAL metrics, not mock data.**
    """
    await manager.connect(websocket)
    try:
        while True:
            # Get REAL metrics from aggregator
            metrics = await get_agent_metrics_data()
            await websocket.send_json(metrics)
            
            # Wait 5 seconds before next update
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from agents metrics WebSocket")
    except Exception as e:
        logger.error(f"Error in agents metrics WebSocket: {e}")
        manager.disconnect(websocket)
