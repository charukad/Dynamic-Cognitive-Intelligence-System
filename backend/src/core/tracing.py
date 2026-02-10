"""
OpenTelemetry / Jaeger Tracing Instrumentation for DCIS Backend

Adds distributed tracing to track requests across the multi-agent system.

Install dependencies:
    pip install opentelemetry-api opentelemetry-sdk
    pip install opentelemetry-instrumentation-fastapi
    pip install opentelemetry-exporter-jaeger

Usage in main.py:
    from backend.src.core.tracing import setup_tracing
    
    app = Fast API()
    setup_tracing(app, service_name="dcis-backend")
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def setup_tracing(
    app,
    service_name: str = "dcis-backend",
    jaeger_host: str = "localhost",
    jaeger_port: int = 6831,
    enabled: bool = True
) -> Optional[trace.Tracer]:
    """
    Setup OpenTelemetry tracing with Jaeger exporter.
    
    Args:
        app: FastAPI application instance
        service_name: Name of the service for tracing
        jaeger_host: Jaeger agent hostname
        jaeger_port: Jaeger agent port (UDP)
        enabled: Enable/disable tracing
    
    Returns:
        Tracer instance if enabled, None otherwise
    """
    if not enabled:
        logger.info("Tracing is disabled")
        return None
    
    try:
        # Create resource with service information
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "0.1.0",
            "deployment.environment": "development"
        })
        
        # Setup tracer provider
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
        
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=jaeger_host,
            agent_port=jaeger_port,
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        
        logger.info(f"Tracing enabled for {service_name} -> {jaeger_host}:{jaeger_port}")
        
        return trace.get_tracer(__name__)
    
    except Exception as e:
        logger.error(f"Failed to setup tracing: {e}")
        return None


def get_tracer() -> trace.Tracer:
    """Get the current tracer instance"""
    return trace.get_tracer(__name__)


def trace_agent_task(agent_name: str, task_type: str):
    """
    Decorator to trace agent task execution.
    
    Usage:
        @trace_agent_task("logician", "reasoning")
        async def  process_task(self, task):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            with tracer.start_as_current_span(
                f"agent.{agent_name}.{task_type}",
                attributes={
                    "agent.name": agent_name,
                    "agent.task_type": task_type
                }
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("task.success", True)
                    return result
                except Exception as e:
                    span.set_attribute("task.success", False)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator


def trace_memory_operation(operation: str):
    """
    Decorator to trace memory system operations.
    
    Usage:
        @trace_memory_operation("store_episodic")
        async def store_memory(self, data):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            with tracer.start_as_current_span(
                f"memory.{operation}",
                attributes={"memory.operation": operation}
            ) as span:
                result = await func(*args, **kwargs)
                
                # Add result metadata
                if isinstance(result, dict):
                    if "memory_id" in result:
                        span.set_attribute("memory.id", result["memory_id"])
                
                return result
        
        return wrapper
    return decorator


class TraceContext:
    """Context manager for manual span creation"""
    
    def __init__(self, span_name: str, attributes: dict = None):
        self.span_name = span_name
        self.attributes = attributes or {}
        self.tracer = get_tracer()
        self.span = None
    
    def __enter__(self):
        self.span = self.tracer.start_span(
            self.span_name,
            attributes=self.attributes
        )
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.span.set_attribute("error", True)
            self.span.set_attribute("error.type", exc_type.__name__)
            self.span.record_exception(exc_val)
        
        self.span.end()
        return False  # Don't suppress exceptions


# Example usage in orchestrator
def trace_query_processing(query: str, max_agents: int = 3):
    """Example: Trace query processing through the system"""
    tracer = get_tracer()
    
    with tracer.start_as_current_span(
        "orchestrator.process_query",
        attributes={
            "query.text": query[:100],  # Truncate long queries
            "query.max_agents": max_agents
        }
    ) as parent_span:
        
        # HTN Planning
        with tracer.start_as_current_span("htn.decompose"):
            # ... HTN decomposition logic
            pass
        
        # Agent Selection
        with tracer.start_as_current_span("router.select_agents"):
            # ... Thompson sampling logic
            pass
        
        # Agent Execution
        with tracer.start_as_current_span("agents.execute"):
            # ... Agent task execution
            pass
        
        parent_span.set_attribute("agents.selected", ["logician", "scholar"])
        parent_span.set_attribute("query.success", True)
