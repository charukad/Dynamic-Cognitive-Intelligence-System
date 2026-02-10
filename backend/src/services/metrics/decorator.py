"""
Metrics Collection Decorators

Reusable decorators for automatic agent execution tracking.
"""

import functools
import logging
from typing import Optional, Any, Callable

from src.services.metrics.collector import get_metrics_collector

logger = logging.getLogger(__name__)


def track_agent_execution(task_type: str = "processing"):
    """
    Decorator to track agent method execution time and success/failure.
    
    Assumes the wrapped method is an async method on a class with 
    a 'agent' attribute (like BaseAgent).
    
    Args:
        task_type: Type of task being executed (e.g., 'analysis', 'visualization')
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            # Try to get agent info from self
            agent_id = "unknown"
            agent_name = "Unknown Agent"
            
            try:
                if hasattr(self, "agent"):
                    # BaseAgent style
                    agent_id = self.agent.id
                    agent_name = self.agent.name
                elif hasattr(self, "agent_id"):
                    # Direct attribute style
                    agent_id = self.agent_id
                    agent_name = getattr(self, "name", "Unnamed Agent")
            except Exception:
                pass
            
            # Generate task ID
            import uuid
            task_id = str(uuid.uuid4())
            
            collector = None
            execution = None
            
            try:
                # 1. Start Tracking
                try:
                    collector = get_metrics_collector()
                    execution = await collector.record_task_start(
                        agent_id=agent_id,
                        agent_name=agent_name,
                        task_id=task_id,
                        task_type=task_type,
                        input_data={"args": str(args), "kwargs": str(kwargs)}
                    )
                except Exception as e:
                    logger.warning(f"Failed to start metrics tracking: {e}")
                
                # 2. Execute Method
                result = await func(self, *args, **kwargs)
                
                # 3. Record Success
                if collector and execution:
                    await collector.record_task_completion(
                        execution=execution,
                        success=True,
                        output_data={"result_summary": "Success"}
                    )
                
                return result
                
            except Exception as e:
                # 4. Record Failure
                if collector and execution:
                    await collector.record_task_completion(
                        execution=execution,
                        success=False,
                        error_type=type(e).__name__,
                        error_message=str(e)
                    )
                raise e
                
        return wrapper
    return decorator
