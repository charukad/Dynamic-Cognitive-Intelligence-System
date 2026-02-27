"""
Main FastAPI Application with Advanced AI Integration

Registers all routes including:
- Specialized agent APIs
- Advanced AI services APIs
- WebSocket endpoints
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from src.core import get_logger
from src.api.v1.agents import (
    data_analyst,
    designer,
    translator,
    financial
)
from src.api.v1.advanced import ai_services
from src.api.v1 import monitoring, memory, agents_metrics, chat
from src.api.routes import (
    monitoring as monitoring_routes,
    memory as memory_routes,
    gaia_evolution,
    orchestrator,
    analytics,
    memory_stats,
    gaia_stats,
    tournaments,
    chat_history,
    chat_sessions,
    chat_feedback,
)
from src.api.websocket.ai_services_ws import (
    ai_services_websocket_endpoint,
    start_status_broadcaster
)
from src.infrastructure.metrics.postgres_repository import PostgreSQLMetricsRepository
from src.infrastructure.metrics.redis_repository import get_cache_repository
from src.services.metrics.collector import initialize_metrics_collector
from src.infrastructure.llm.vllm_client import vllm_client

logger = get_logger(__name__)

# ============================================================================
# Create FastAPI App
# ============================================================================

app = FastAPI(
    title="DCIS API",
    description="Dynamic Cognitive Intelligence System - Enterprise AI Orchestration",
    version="1.0.0"
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monitoring middleware - tracks all requests
from src.middleware.monitoring import MonitoringMiddleware
app.add_middleware(MonitoringMiddleware)

# ============================================================================
# Register Routers
# ============================================================================

# Specialized Agents
app.include_router(data_analyst.router, prefix="/api")
app.include_router(designer.router, prefix="/api")
app.include_router(translator.router, prefix="/api")
app.include_router(financial.router, prefix="/api")

# Advanced AI Services
app.include_router(ai_services.router, prefix="/api")

# Monitoring & Memory (v1 endpoints)
app.include_router(monitoring.router, prefix="/api")
app.include_router(memory.router, prefix="/api")

# Routes endpoints (comprehensive)
app.include_router(monitoring_routes.router, prefix="/api/v1")
app.include_router(memory_routes.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(gaia_evolution.router, prefix="/api/v1")
app.include_router(orchestrator.router, prefix="/api/v1")
app.include_router(tournaments.router, prefix="/api/v1")

# Agents Metrics (HTTP + WebSocket)
app.include_router(agents_metrics.router, prefix="/api")

# General Chat
app.include_router(chat.router, prefix="/api/v1")

# Chat History
app.include_router(chat_history.router, prefix="/api/v1")
app.include_router(chat_sessions.router, prefix="/api/v1")
app.include_router(chat_feedback.router, prefix="/api/v1")

# Analytics
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(memory_stats.router, prefix="/api/v1")
app.include_router(gaia_stats.router, prefix="/api/v1")

# Test utilities (remove in production)


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@app.websocket("/ws/ai-services")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for AI services real-time updates"""
    await ai_services_websocket_endpoint(websocket)

# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting DCIS API Server")
    logger.info("📊 Specialized Agents: Data Analyst, Designer, Translator, Financial Advisor")
    logger.info("🧠 Advanced AI: Oneiroi Dreaming, GAIA Tournaments, Multi-modal Processing")
    logger.info("🔌 WebSocket: Real-time updates enabled")
    
    # Start background status broadcaster
    asyncio.create_task(start_status_broadcaster())

    # Connect to LLM
    try:
        await vllm_client.connect()
    except Exception as e:
        logger.error(f"Failed to connect to LLM: {e}")
    
    # Initialize Metrics Collector Service
    try:
        cache_repo = await get_cache_repository()
        db_repo = PostgreSQLMetricsRepository()
        initialize_metrics_collector(db_repo, cache_repo)
        logger.info("⚡ Metrics Collector Service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Metrics Collector: {e}", exc_info=True)
    
    
    logger.info("✅ DCIS API Server Ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down DCIS API Server")
    
    # Close vLLM client if it has a close method
    if hasattr(vllm_client, 'close'):
        try:
            await vllm_client.close()
        except Exception as e:
            logger.warning(f"Error closing vLLM client: {e}")



# ============================================================================
# Agent Registry Endpoint
# ============================================================================

@app.get("/api/v1/agents")
async def list_agents():
    """List available specialized agents"""
    return [
        {
            "id": "data-analyst", 
            "name": "Data Analyst Agent", 
            "description": "Specialized in data analysis and visualization",
            "capabilities": ["data_analysis", "visualization", "pandas", "matplotlib"]
        },
        {
            "id": "designer", 
            "name": "Designer Agent", 
            "description": "Generates UI/UX designs and mockups",
            "capabilities": ["ui_design", "mockups", "figma_integration"]
        },
        {
            "id": "financial", 
            "name": "Financial Advisor Agent", 
            "description": "Analyzes financial data and trends",
            "capabilities": ["financial_analysis", "forecasting", "reporting"]
        },
        {
            "id": "translator", 
            "name": "Translator Agent", 
            "description": "Provides multi-lingual translation services",
            "capabilities": ["translation", "language_detection"]
        }
    ]


@app.get("/api/v1/agents/performance-history")
async def get_agent_performance(range: str = "7d"):
    """Get agent performance history over time"""
    import time
    from datetime import datetime, timedelta
    
    # Generate mock timestamps for the last 7 days
    now = datetime.now()
    timestamps = [(now - timedelta(days=i)).isoformat() for i in range(7, 0, -1)]
    
    return {
        "agents": [
            {
                "id": "data-analyst",
                "name": "Data Analyst",
                "metrics": [
                    {
                        "timestamp": ts,
                        "success_rate": 0.92 + (i * 0.01),
                        "avg_latency_ms": 120 - (i * 5),
                        "tasks_completed": 100 + (i * 10)
                    }
                    for i, ts in enumerate(timestamps)
                ]
            },
            {
                "id": "designer",
                "name": "Designer",
                "metrics": [
                    {
                        "timestamp": ts,
                        "success_rate": 0.88 + (i * 0.015),
                        "avg_latency_ms": 200 - (i * 8),
                        "tasks_completed": 50 + (i * 5)
                    }
                    for i, ts in enumerate(timestamps)
                ]
            },
            {
                "id": "financial",
                "name": "Financial Advisor",
                "metrics": [
                    {
                        "timestamp": ts,
                        "success_rate": 0.95 + (i * 0.005),
                        "avg_latency_ms": 150 - (i * 6),
                        "tasks_completed": 80 + (i * 8)
                    }
                    for i, ts in enumerate(timestamps)
                ]
            },
            {
                "id": "translator",
                "name": "Translator",
                "metrics": [
                    {
                        "timestamp": ts,
                        "success_rate": 0.97 + (i * 0.003),
                        "avg_latency_ms": 90 - (i * 3),
                        "tasks_completed": 150 + (i * 15)
                    }
                    for i, ts in enumerate(timestamps)
                ]
            }
        ],
        "range": range,
        "timestamp": int(time.time())
    }


# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "DCIS API",
        "version": "1.0.0",
        "description": "Dynamic Cognitive Intelligence System - Enterprise AI Orchestration",
        "features": {
            "specialized_agents": 4,
            "advanced_ai_services": 3,
            "api_endpoints": "50+",
            "websocket": True
        },
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "api": "online",
            "websocket": "online",
            "agents": "online",
            "advanced_ai": "online"
        }
    }
