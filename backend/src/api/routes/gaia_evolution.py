"""
GAIA Evolution API endpoints for agent self-improvement.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.advanced.gaia.evolution_engine import (
    evolution_engine,
    EvolutionGenome,
    EvolutionMetrics,
)
from src.services.advanced.gaia.meta_learner import meta_learner

router = APIRouter(prefix="/gaia/evolution", tags=["gaia-evolution"])


# ============================================================================
# Request/Response Models
# ============================================================================

class FitnessMetricsRequest(BaseModel):
    """Metrics for fitness evaluation."""
    
    agent_id: str
    success_rate: float = Field(ge=0.0, le=1.0)
    avg_response_time: float = Field(ge=0.0)
    user_satisfaction: float = Field(ge=0.0, le=1.0, default=0.5)
    task_completion: float = Field(ge=0.0, le=1.0, default=0.5)
    elo_rating: float = Field(ge=0.0, default=1000.0)


class GenomeResponse(BaseModel):
    """Genome response."""
    
    agent_id: str
    system_prompt: str
    temperature: float
    capabilities: List[str]
    fitness_score: float
    generation: int


class EvolutionStatsResponse(BaseModel):
    """Evolution statistics."""
    
    current_generation: int
    population_size: int
    avg_fitness: float
    best_fitness: float
    best_genome: Optional[GenomeResponse]


class StrategyResponse(BaseModel):
    """Successful strategy response."""
    
    id: str
    task_pattern: str
    strategy_description: str
    avg_success_rate: float
    usage_count: int


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/evolve")
async def evolve_generation(metrics_list: List[FitnessMetricsRequest]) -> Dict[str, Any]:
    """
    Evolve one generation of agents.
    
    Args:
        metrics_list: Performance metrics for current population
        
    Returns:
        New evolved population
    """
    try:
        # Convert metrics to internal format
        population_metrics = []
        
        for metrics_req in metrics_list:
            # Create genome (mock for now - replace with DB fetch)
            genome = EvolutionGenome(
                agent_id=UUID(metrics_req.agent_id),
                system_prompt="You are a helpful AI assistant.",
                temperature=0.7,
                capabilities=["reasoning", "analysis"],
            )
            
            metrics = EvolutionMetrics(
                success_rate=metrics_req.success_rate,
                avg_response_time=metrics_req.avg_response_time,
                user_satisfaction=metrics_req.user_satisfaction,
                task_completion=metrics_req.task_completion,
                elo_rating=metrics_req.elo_rating,
            )
            
            population_metrics.append((genome, metrics))
        
        # Evolve
        new_population = await evolution_engine.evolve_generation(population_metrics)
        
        return {
            "generation": evolution_engine.current_generation,
            "population": [g.to_dict() for g in new_population],
            "best_fitness": new_population[0].fitness_score if new_population else 0.0,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evolution failed: {str(e)}"
        )


@router.get("/stats", response_model=EvolutionStatsResponse)
async def get_evolution_stats() -> EvolutionStatsResponse:
    """Get evolution statistics."""
    
    avg_fitness = (
        sum(g.fitness_score for g in evolution_engine.population) / 
        len(evolution_engine.population) if evolution_engine.population else 0.0
    )
    
    best_genome_data = None
    if evolution_engine.best_genome:
        best_genome_data = GenomeResponse(
            agent_id=str(evolution_engine.best_genome.agent_id),
            system_prompt=evolution_engine.best_genome.system_prompt,
            temperature=evolution_engine.best_genome.temperature,
            capabilities=evolution_engine.best_genome.capabilities,
            fitness_score=evolution_engine.best_genome.fitness_score,
            generation=evolution_engine.best_genome.generation,
        )
    
    return EvolutionStatsResponse(
        current_generation=evolution_engine.current_generation,
        population_size=len(evolution_engine.population),
        avg_fitness=avg_fitness,
        best_fitness=evolution_engine.best_genome.fitness_score if evolution_engine.best_genome else 0.0,
        best_genome=best_genome_data,
    )


@router.post("/meta-learn/store")
async def store_successful_strategy(
    task_description: str,
    agent_config: Dict[str, Any],
    success_metrics: Dict[str, float],
) -> Dict[str, Any]:
    """Store a successful strategy."""
    
    try:
        strategy = meta_learner.store_success(
            task_description=task_description,
            agent_config=agent_config,
            success_metrics=success_metrics,
        )
        
        return strategy.to_dict()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store strategy: {str(e)}"
        )


@router.get("/meta-learn/retrieve", response_model=List[StrategyResponse])
async def retrieve_strategies(task_description: str, top_k: int = 3) -> List[StrategyResponse]:
    """Retrieve similar successful strategies."""
    
    try:
        strategies = meta_learner.retrieve_strategy(task_description, top_k)
        
        return [
            StrategyResponse(
                id=str(s.id),
                task_pattern=s.task_pattern,
                strategy_description=s.strategy_description,
                avg_success_rate=s.avg_success_rate,
                usage_count=s.usage_count,
            )
            for s in strategies
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve strategies: {str(e)}"
        )


@router.get("/meta-learn/stats")
async def get_meta_learning_stats() -> Dict[str, Any]:
    """Get meta-learning statistics."""
    return meta_learner.get_statistics()
