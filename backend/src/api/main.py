"""FastAPI application factory."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware import LoggingMiddleware, RequestIDMiddleware
from src.core import get_logger, settings, setup_logging
from src.api.routes import health

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan events."""
    # Import lifecycle manager
    from src.core.lifecycle import lifecycle_manager
    
    # Startup
    logger.info("Starting DCIS application...")
    await lifecycle_manager.startup()
    
    yield
    
    # Shutdown
    logger.info("Shutting down DCIS application...")
    await lifecycle_manager.shutdown()



def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,  # ✅ Fixed: lowercase to match config.py
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # Include routers
    app.include_router(health.router, tags=["health"])
    
    # Import and include v1 routers
    from src.api.routes import advanced, agents, memory, memory_viz, memory_management, query, tasks, mirror, contrastive, causal, gnn, graph, websocket, orchestrator, gaia_evolution, advanced_intelligence, monitoring, mlops, rlhf, analytics
    app.include_router(agents.router, prefix=settings.api_v1_prefix)
    app.include_router(tasks.router, prefix=settings.api_v1_prefix)
    app.include_router(query.router, prefix=settings.api_v1_prefix)
    app.include_router(memory.router, prefix=settings.api_v1_prefix)
    app.include_router(memory_viz.router, prefix=settings.api_v1_prefix) # Memory visualization
    app.include_router(memory_management.router, prefix=settings.api_v1_prefix)  # Memory optimization
    app.include_router(advanced.router, prefix=settings.api_v1_prefix)
    app.include_router(orchestrator.router, prefix=settings.api_v1_prefix)  # HTN Planner visualization
    app.include_router(gaia_evolution.router, prefix=settings.api_v1_prefix)  # GAIA Evolution
    app.include_router(advanced_intelligence.router, prefix=settings.api_v1_prefix)  # Mirror + Neurosymbolic + Temporal
    app.include_router(monitoring.router, prefix=settings.api_v1_prefix)  # Production monitoring
    app.include_router(mlops.router, prefix=settings.api_v1_prefix)  # Model versioning & A/B testing
    app.include_router(rlhf.router, prefix=settings.api_v1_prefix)  # Human feedback & reward modeling
    from src.api.routes import gaia
    app.include_router(gaia.router, prefix=settings.api_v1_prefix)  # General GAIA stats
    app.include_router(analytics.router, prefix=settings.api_v1_prefix)  # Unified analytics
    app.include_router(mirror.router, prefix=settings.api_v1_prefix)  # Mirror Protocol
    app.include_router(contrastive.router, prefix=settings.api_v1_prefix)  # Contrastive Learning
    app.include_router(causal.router, prefix=settings.api_v1_prefix)  # Causal Reasoning
    app.include_router(gnn.router, prefix=settings.api_v1_prefix)  # Graph Neural Networks
    app.include_router(graph.router, prefix=settings.api_v1_prefix) # Graph router
    
    # WebSocket endpoint - native FastAPI WebSocket (not Socket.IO)
    app.include_router(websocket.router)  # Endpoint: /ws/ai-services

    return app


# Create app instance
app = create_app()
