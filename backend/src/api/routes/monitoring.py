"""
Monitoring & Operations API

Unified endpoints for production monitoring, metrics, and health checks.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, status

from src.services.monitoring.metrics import metrics_collector, tracer
from src.services.resilience.circuit_breaker import default_circuit_breaker
from src.services.caching.cache_manager import cache_manager

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


# ============================================================================
# Metrics Endpoints
# ============================================================================

@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get all metrics summary."""
    return metrics_collector.get_all_metrics_summary()


@router.get("/metrics/{name}")
async def get_metric_history(name: str, limit: int = 100) -> Dict[str, Any]:
    """Get metric history."""
    return {
        'metric_name': name,
        'history': metrics_collector.get_recent_metrics(name, limit),
    }


@router.get("/metrics/histogram/{name}")
async def get_histogram_stats(name: str) -> Dict[str, Any]:
    """Get histogram statistics."""
    return {
        'metric_name': name,
        'stats': metrics_collector.get_histogram_stats(name),
    }


# ============================================================================
# Tracing Endpoints
# ============================================================================

@router.get("/traces/recent")
async def get_recent_traces(limit: int = 100) -> Dict[str, Any]:
    """Get recent request traces."""
    return {
        'traces': tracer.get_recent_traces(limit),
        'total': len(tracer.completed_traces),
    }


@router.get("/traces/active")
async def get_active_traces() -> Dict[str, Any]:
    """Get currently active traces."""
    return {
        'traces': tracer.get_active_traces(),
        'count': len(tracer.active_traces),
    }


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str) -> Dict[str, Any]:
    """Get specific trace by ID."""
    from uuid import UUID
    
    trace = tracer.get_trace(UUID(trace_id))
    if not trace:
        return {'error': 'Trace not found'}
    
    return trace.to_dict()


# ============================================================================
# Circuit Breaker Endpoints
# ============================================================================

@router.get("/circuit-breaker/stats")
async def get_circuit_breaker_stats() -> Dict[str, Any]:
    """Get circuit breaker statistics."""
    return default_circuit_breaker.get_stats()


@router.post("/circuit-breaker/reset")
async def reset_circuit_breaker() -> Dict[str, Any]:
    """Reset circuit breaker to closed state."""
    default_circuit_breaker.reset()
    return {'message': 'Circuit breaker reset', 'state': 'closed'}


# ============================================================================
# Cache Endpoints
# ============================================================================

@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return cache_manager.get_stats()


@router.delete("/cache/clear")
async def clear_cache() -> Dict[str, Any]:
    """Clear all caches."""
    cache_manager.clear()
    return {'message': 'Cache cleared'}


@router.delete("/cache/{key}")
async def delete_cache_key(key: str) -> Dict[str, Any]:
    """Delete specific cache key."""
    success = cache_manager.delete(key)
    return {'key': key, 'deleted': success}


# ============================================================================
# Health Check Endpoints
# ============================================================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check."""
    # Check circuit breaker
    cb_stats = default_circuit_breaker.get_stats()
    cb_healthy = cb_stats['state'] != 'open'
    
    # Check cache
    cache_stats = cache_manager.get_stats()
    cache_healthy = cache_stats['l1']['hit_rate'] > 0.3 if cache_stats['l1']['total_gets'] > 100 else True
    
    # Overall health
    all_healthy = cb_healthy and cache_healthy
    
    return {
        'status': 'healthy' if all_healthy else 'degraded',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'circuit_breaker': {
                'healthy': cb_healthy,
                'state': cb_stats['state'],
                'failure_rate': cb_stats.get('failure_rate', 0.0),
            },
            'cache': {
                'healthy': cache_healthy,
                'hit_rate': cache_stats['l1']['hit_rate'],
                'utilization': cache_stats['l1']['utilization'],
            },
        },
    }


@router.get("/health/liveness")
async def liveness_probe() -> Dict[str, str]:
    """Kubernetes liveness probe."""
    return {'status': 'alive'}


@router.get("/health/readiness")
async def readiness_probe() -> Dict[str, Any]:
    """Kubernetes readiness probe."""
    cb_stats = default_circuit_breaker.get_stats()
    ready = cb_stats['state'] != 'open'
    
    return {
        'status': 'ready' if ready else 'not_ready',
        'circuit_breaker_state': cb_stats['state'],
    }


# ============================================================================
# Performance Dashboard Data
# ============================================================================

@router.get("/dashboard/overview")
async def get_dashboard_overview() -> Dict[str, Any]:
    """Get data for monitoring dashboard."""
    # Metrics
    metrics_summary = metrics_collector.get_all_metrics_summary()
    
    # Circuit breaker
    cb_stats = default_circuit_breaker.get_stats()
    
    # Cache
    cache_stats = cache_manager.get_stats()
    
    # Traces
    recent_traces = tracer.get_recent_traces(10)
    active_trace_count = len(tracer.active_traces)
    
    # Calculate average latency from traces
    avg_latency = 0.0
    if recent_traces:
        latencies = [t['duration_ms'] for t in recent_traces if t['duration_ms']]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    
    return {
        'timestamp': datetime.now().isoformat(),
        'metrics': {
            'total_requests': metrics_summary.get('counters', {}).get('requests', 0),
            'avg_latency_ms': avg_latency,
            'error_rate': metrics_summary.get('counters', {}).get('errors', 0),
        },
        'circuit_breaker': {
            'state': cb_stats['state'],
            'success_rate': cb_stats['success_rate'],
            'failure_rate': cb_stats['failure_rate'],
        },
        'cache': {
            'hit_rate': cache_stats['l1']['hit_rate'],
            'size': cache_stats['l1']['current_size'],
            'utilization': cache_stats['l1']['utilization'],
        },
        'tracing': {
            'active_traces': active_trace_count,
            'recent_traces': len(recent_traces),
        },
    }
