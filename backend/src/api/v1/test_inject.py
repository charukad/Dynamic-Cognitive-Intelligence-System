"""
Test Data Injection API

Temporary endpoint to inject test agent activity data for demonstration.
This allows testing the metrics system without needing to instrument actual agents.
"""

from fastapi import APIRouter
from typing import Dict, Any
import random
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/v1/test/inject-metrics")
async def inject_test_metrics() -> Dict[str, Any]:
    """
    Inject test metrics data for demonstration purposes.
    
    Creates simulated agent activity data directly in the metrics cache
    to demonstrate the real metrics system working.
    
   **WARNING: This is for testing/demo only. Remove in production.**
    """
    try:
        from src.api.v1.agents_metrics import get_aggregator
        
        aggregator = await get_aggregator()
        cache = aggregator.cache
        
        logger.info("Injecting test metrics data...")
        
        # Define agents
        agents = [
            ("data-analyst", "Data Analyst"),
            ("designer", "Designer"),
            ("financial", "Financial Advisor"),
            ("translator", "Translator")
        ]
        
        # Inject task counts and response times
        for agent_id, _ in agents:
            # Random task counts
            total_tasks = random.randint(10, 50)
            successful = int(total_tasks * random.uniform(0.75, 0.95))
            failed = total_tasks - successful
            
            # Update cache directly
            key = f"agent:{agent_id}:metrics"
            cache._memory_cache[key] = {
                "total_tasks": total_tasks,
                "successful_tasks": successful,
                "failed_tasks": failed
            }
            
            # Inject response times
            response_times = [random.randint(200, 1200) for _ in range(20)]
            cache._memory_cache[f"agent:{agent_id}:response_times"] = response_times
            
            # Set random ELO
            elo = random.randint(1400, 1600)
            cache._memory_cache[f"agent:{agent_id}:elo"] = elo
            
            # Add dream/insight counts
            cache._memory_cache[key]["dream_cycles"] = random.randint(2, 8)
            cache._memory_cache[key]["insights"] = random.randint(5, 25)
        
        # Get current metrics to return
        metrics = await aggregator.get_all_agents_metrics()
        
        logger.info("Test metrics injected successfully")
        
        return {
            "success": True,
            "message": "Test metrics injected successfully",
            "agents": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to inject test metrics: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
