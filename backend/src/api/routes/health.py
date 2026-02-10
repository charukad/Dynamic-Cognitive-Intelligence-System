"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    service: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        HealthResponse: Service health status
    """
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        service="DCIS Backend",
    )


@router.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "DCIS - Distributed Collective Intelligence System",
        "version": "0.1.0",
        "docs": "/docs",
    }
