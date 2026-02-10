"""Logging middleware for FastAPI."""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    
    Logs request details, response status, and processing time.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Process request and log details.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain
            
        Returns:
            HTTP response
        """
        # Start timer
        start_time = time.time()
        
        # Extract request details
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        
        # Log incoming request
        logger.info(
            f"Incoming request: {method} {url}",
            extra={
                "method": method,
                "url": url,
                "client": client_host,
                "headers": dict(request.headers),
            },
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Add custom header
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
            
            # Log response
            logger.info(
                f"Response: {method} {url} - {response.status_code} ({process_time:.2f}ms)",
                extra={
                    "method": method,
                    "url": url,
                    "status_code": response.status_code,
                    "process_time_ms": process_time,
                },
            )
            
            return response
            
        except Exception as e:
            # Log error
            process_time = (time.time() - start_time) * 1000
            
            logger.error(
                f"Request failed: {method} {url} - {str(e)} ({process_time:.2f}ms)",
                extra={
                    "method": method,
                    "url": url,
                    "error": str(e),
                    "process_time_ms": process_time,
                },
                exc_info=True,
            )
            
            # Re-raise exception to be handled by error middleware
            raise


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding request ID to all requests.
    
    Useful for tracing requests through the system.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Add request ID to request state.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain
            
        Returns:
            HTTP response with request ID header
        """
        import uuid
        
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Add to request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware.
    
    Limits requests per client IP.
    """

    def __init__(self, app, requests_per_minute: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per IP
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: dict = {}  # IP -> (timestamp, count)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Check rate limit and process request.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain
            
        Returns:
            HTTP response or 429 Too Many Requests
        """
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Get or initialize request count for this IP
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = (current_time, 0)
        
        last_reset, count = self.request_counts[client_ip]
        
        # Reset counter if a minute has passed
        if current_time - last_reset >= 60:
            self.request_counts[client_ip] = (current_time, 1)
        else:
            # Increment counter
            count += 1
            self.request_counts[client_ip] = (last_reset, count)
            
            # Check if limit exceeded
            if count > self.requests_per_minute:
                logger.warning(
                    f"Rate limit exceeded for {client_ip}",
                    extra={"client_ip": client_ip, "count": count},
                )
                
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Maximum {self.requests_per_minute} requests per minute",
                    },
                )
        
        # Process request
        return await call_next(request)
