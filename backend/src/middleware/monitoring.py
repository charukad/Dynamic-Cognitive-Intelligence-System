"""
Request Monitoring Middleware

Automatically tracks all API requests through the monitoring infrastructure.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.services.monitoring.metrics import metrics_collector, tracer


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically track all API requests.
    
    Collects:
    - Request counts
    - Response latencies  
    - Error rates
    - Status codes
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timing
        start_time = time.time()
        
        # Start distributed trace
        trace = tracer.start_trace(
            operation=f"{request.method} {request.url.path}",
            metadata={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            metrics_collector.increment_counter("requests", tags={
                "method": request.method,
                "path": request.url.path,
                "status": str(response.status_code),
            })
            
            metrics_collector.record_histogram("request_latency_ms", duration_ms, tags={
                "method": request.method,
                "path": request.url.path,
            })
            
            # Record error if status >= 400
            if response.status_code >= 400:
                metrics_collector.increment_counter("errors", tags={
                    "method": request.method,
                    "path": request.url.path,
                    "status": str(response.status_code),
                })
            
            # Finish trace
            tracer.finish_trace(trace.span_id)
            
            return response
            
        except Exception as e:
            # Record error
            metrics_collector.increment_counter("errors", tags={
                "method": request.method,
                "path": request.url.path,
                "error": type(e).__name__,
            })
            
            # Mark trace as error
            trace.metadata["error"] = str(e)
            trace.status = "error"
            tracer.finish_trace(trace.span_id)
            
            raise
