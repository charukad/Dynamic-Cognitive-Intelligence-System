"""
Monitoring API Router

Provides system monitoring endpoints with REAL data from:
- Dashboard overview metrics (real cache, circuit breaker, traces)
- Cache statistics (from cache_manager)
- Circuit breaker stats (from circuit_breaker)
- Administrative actions
"""

from fastapi import APIRouter
from typing import Dict, Any

from src.services.monitoring.metrics import metrics_collector, tracer
from src.services.resilience.circuit_breaker import default_circuit_breaker
from src.services.caching.cache_manager import cache_manager

router = APIRouter(tags=["Monitoring"])

# ============================================================================
# Dashboard Overview - REAL DATA
# ============================================================================

@router.get("/v1/monitoring/dashboard/overview")
async def get_dashboard_overview() -> Dict[str, Any]:
    """Get system monitoring overview metrics - ALL REAL DATA"""
    
    # Get real metrics summary
    metrics_summary = metrics_collector.get_all_metrics_summary()
    
    # Get real circuit breaker stats
    cb_stats = default_circuit_breaker.get_stats()
    
    # Get real cache stats
    cache_stats = cache_manager.get_stats()
    
    # Get real trace counts
    active_trace_count = len(tracer.active_traces)
    recent_traces = tracer.get_recent_traces(100)
    
    # Calculate real average latency from traces
    avg_latency = 0.0
    if recent_traces:
        latencies = [t['duration_ms'] for t in recent_traces if t.get('duration_ms')]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    
    # Get total request count from metrics
    total_requests = metrics_summary.get('counters', {}).get('requests', 0)
    error_count = metrics_summary.get('counters', {}).get('errors', 0)
    
    return {
        "timestamp": metrics_summary.get('timestamp', ''),
        "metrics": {
            "total_requests": total_requests,
            "avg_latency_ms": round(avg_latency, 1),
            "error_rate": error_count
        },
        "circuit_breaker": {
            "state": cb_stats['state'],
            "success_rate": cb_stats['success_rate'],
            "failure_rate": cb_stats['failure_rate']
        },
        "cache": {
            "hit_rate": cache_stats['l1']['hit_rate'],
            "size": cache_stats['l1']['current_size'],
            "utilization": cache_stats['l1']['utilization']
        },
        "tracing": {
            "active_traces": active_trace_count,
            "recent_traces": len(recent_traces)
        }
    }


# ============================================================================
# Cache Statistics - REAL DATA
# ============================================================================

@router.get("/v1/monitoring/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """Get Redis cache statistics - REAL DATA from cache_manager"""
    return cache_manager.get_stats()


# ============================================================================
# Circuit Breaker Statistics - REAL DATA
# ============================================================================

@router.get("/v1/monitoring/circuit-breaker/stats")
async def get_circuit_breaker_stats() -> Dict[str, Any]:
    """Get circuit breaker statistics - REAL DATA"""
    return default_circuit_breaker.get_stats()


# ============================================================================
# Administrative Actions - REAL IMPLEMENTATIONS
# ============================================================================

@router.delete("/v1/monitoring/cache/clear")
async def clear_cache() -> Dict[str, str]:
    """Clear system cache - REAL ACTION"""
    cache_manager.clear()
    return {
        "status": "success",
        "message": "Cache cleared successfully"
    }


@router.post("/v1/monitoring/circuit-breaker/reset")
async def reset_circuit_breaker() -> Dict[str, str]:
    """Reset circuit breakers to closed state - REAL ACTION"""
    default_circuit_breaker.reset()
    return {
        "status": "success",
        "message": "Circuit breaker reset successfully"
    }
