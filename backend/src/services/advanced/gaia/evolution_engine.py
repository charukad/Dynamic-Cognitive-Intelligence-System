"""
GAIA Evolution Engine - Genetic Algorithm for Agent Self-Improvement

Implements evolutionary strategies to automatically optimize agent configurations:
- Genetic mutations of system prompts and hyperparameters
- Crossover breeding between high-performing agents
- Fitness evaluation based on success metrics
- Automated selection and reproduction
"""

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from src.core import get_logger
from src.domain.models import Agent
from src.infrastructure.llm.vllm_client import vllm_client

logger = get_logger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class EvolutionGenome:
    """Genetic representation of an agent's configuration."""
    
    agent_id: UUID
    system_prompt: str
    temperature: float
    capabilities: List[str]
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    fitness_score: float = 0.0
    generation: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'agent_id': str(self.agent_id),
            'system_prompt': self.system_prompt,
            'temperature': self.temperature,
            'capabilities': self.capabilities,
            'hyperparameters': self.hyperparameters,
            'fitness_score': self.fitness_score,
            'generation': self.generation,
        }


@dataclass
class EvolutionMetrics:
    """Fitness metrics for agent performance."""
    
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    user_satisfaction: float = 0.0
    task_completion: float = 0.0
    elo_rating: float = 1000.0
    
    def calculate_fitness(self) -> float:
        """
        Calculate composite fitness score.
        
        Returns:
            Fitness score (0.0 to 1.0)
        """
        # Weighted combination of metrics
        fitness = (
            self.success_rate * 0.4 +
            (1.0 - min(self.avg_response_time / 5000, 1.0)) * 0.2 +
            self.user_satisfaction * 0.2 +
            self.task_completion * 0.1 +
            min(self.elo_rating / 2000, 1.0) * 0.1
        )
        return max(0.0, min(1.0, fitness))


# ============================================================================
# Evolution Engine
# ============================================================================

class EvolutionEngine:
    """
    Genetic algorithm engine for agent evolution.
    
    Uses natural selection principles to breed better agents:
    1. Evaluate fitness of current population
    2. Select top performers for reproduction
    3. Create offspring via crossover and mutation
    4. Replace weakest agents with offspring
    """
    
    def __init__(
        self,
        population_size: int = 20,
        mutation_rate: float = 0.15,
        crossover_rate: float = 0.7,
        elite_percentage: float = 0.2,
    ):
        """
        Initialize evolution engine.
        
        Args:
            population_size: Number of agents in population
            mutation_rate: Probability of mutation (0.0 to 1.0)
            crossover_rate: Probability of crossover (0.0 to 1.0)
            elite_percentage: Percentage of top performers to preserve
        """
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_count = int(population_size * elite_percentage)
        
        self.current_generation = 0
        self.population: List[EvolutionGenome] = []
        self.best_genome: Optional[EvolutionGenome] = None
        
        logger.info(
            f"Initialized Evolution Engine: "
            f"pop_size={population_size}, "
            f"mutation_rate={mutation_rate}, "
            f"crossover_rate={crossover_rate}"
        )
    
    def evaluate_fitness(
        self,
        genome: EvolutionGenome,
        metrics: EvolutionMetrics
    ) -> float:
        """
        Evaluate fitness of a genome.
        
        Args:
            genome: Agent genome to evaluate
            metrics: Performance metrics
            
        Returns:
            Fitness score
        """
        fitness = metrics.calculate_fitness()
        genome.fitness_score = fitness
        
        logger.debug(f"Evaluated genome {genome.agent_id}: fitness={fitness:.3f}")
        return fitness
    
    def select_parents(self) -> Tuple[EvolutionGenome, EvolutionGenome]:
        """
        Select two parents using tournament selection.
        
        Returns:
            Tuple of two parent genomes
        """
        tournament_size = 3
        
        def tournament():
            candidates = random.sample(self.population, tournament_size)
            return max(candidates, key=lambda g: g.fitness_score)
        
        parent1 = tournament()
        parent2 = tournament()
        
        return parent1, parent2
    
    def crossover(
        self,
        parent1: EvolutionGenome,
        parent2: EvolutionGenome
    ) -> EvolutionGenome:
        """
        Create offspring via crossover.
        
        Args:
            parent1: First parent
            parent2: Second parent
            
        Returns:
            New offspring genome
        """
        if random.random() > self.crossover_rate:
            # No crossover, clone parent
            return self._clone_genome(random.choice([parent1, parent2]))
        
        # Crossover system prompts (take best parts from each)
        prompt1_parts = parent1.system_prompt.split('. ')
        prompt2_parts = parent2.system_prompt.split('. ')
        
        # Randomly mix prompt parts
        offspring_prompt_parts = []
        for p1, p2 in zip(prompt1_parts, prompt2_parts):
            offspring_prompt_parts.append(random.choice([p1, p2]))
        
        offspring_prompt = '. '.join(offspring_prompt_parts)
        
        # Crossover capabilities (union of both parents)
        offspring_capabilities = list(set(parent1.capabilities + parent2.capabilities))
        
        # Average temperature
        offspring_temperature = (parent1.temperature + parent2.temperature) / 2
        
        # Mix hyperparameters
        offspring_hyperparams = {
            **parent1.hyperparameters,
            **random.choice([parent1, parent2]).hyperparameters
        }
        
        offspring = EvolutionGenome(
            agent_id=uuid4(),
            system_prompt=offspring_prompt,
            temperature=offspring_temperature,
            capabilities=offspring_capabilities,
            hyperparameters=offspring_hyperparams,
            generation=self.current_generation + 1,
        )
        
        logger.debug(f"Crossover: {parent1.agent_id} + {parent2.agent_id} -> {offspring.agent_id}")
        return offspring
    
    async def mutate(self, genome: EvolutionGenome) -> EvolutionGenome:
        """
        Apply random mutations to genome.
        
        Args:
            genome: Genome to mutate
            
        Returns:
            Mutated genome (modified in place)
        """
        if random.random() > self.mutation_rate:
            return genome
        
        mutation_type = random.choice([
            'temperature',
            'prompt_modifier',
            'capability_add',
            'capability_remove',
        ])
        
        if mutation_type == 'temperature':
            # Mutate temperature (+/- 0.1)
            genome.temperature = max(0.0, min(2.0, genome.temperature + random.uniform(-0.1, 0.1)))
            logger.debug(f"Mutation: temperature -> {genome.temperature:.2f}")
            
        elif mutation_type == 'prompt_modifier':
            # LLM-based prompt mutation
            try:
                prompt = f"""
                Rewrite the following system prompt to be slightly different, optimizing for better performance.
                Keep the core intent but vary the phrasing or add constraints.
                
                Original Prompt: "{genome.system_prompt}"
                
                New Prompt:
                """
                
                new_prompt = await vllm_client.generate(prompt, max_tokens=200, temperature=0.9)
                
                # Cleanup if needed
                new_prompt = new_prompt.strip().strip('"')
                
                if new_prompt and len(new_prompt) > 10:
                    genome.system_prompt = new_prompt
                    logger.debug(f"Mutation: LLM rewrote prompt")
                else:
                    raise ValueError("Empty or invalid LLM response")
                    
            except Exception as e:
                logger.warning(f"LLM mutation failed, falling back to simple modifier: {e}")
                # Fallback to simple modifier
                modifiers = [
                    "Be more concise.",
                    "Provide detailed explanations.",
                    "Focus on accuracy over speed.",
                    "Prioritize creative solutions.",
                ]
                genome.system_prompt += " " + random.choice(modifiers)
            
        elif mutation_type == 'capability_add':
            # Add random capability
            new_caps = ['reasoning', 'creativity', 'analysis', 'synthesis']
            available = [c for c in new_caps if c not in genome.capabilities]
            if available:
                genome.capabilities.append(random.choice(available))
                logger.debug(f"Mutation: added capability")
                
        elif mutation_type == 'capability_remove':
            # Remove random capability
            if len(genome.capabilities) > 1:
                genome.capabilities.pop(random.randint(0, len(genome.capabilities) - 1))
                logger.debug(f"Mutation: removed capability")
        
        return genome
    
    async def evolve_generation(self, population_metrics: List[Tuple[EvolutionGenome, EvolutionMetrics]]) -> List[EvolutionGenome]:
        """
        Evolve one generation.
        
        Args:
            population_metrics: List of (genome, metrics) tuples
            
        Returns:
            New population
        """
        # Evaluate fitness for all genomes
        for genome, metrics in population_metrics:
            self.evaluate_fitness(genome, metrics)
        
        self.population = [g for g, _ in population_metrics]
        
        # Sort by fitness
        self.population.sort(key=lambda g: g.fitness_score, reverse=True)
        
        # Track best genome
        if not self.best_genome or self.population[0].fitness_score > self.best_genome.fitness_score:
            self.best_genome = self._clone_genome(self.population[0])
            logger.info(f"New best genome: fitness={self.best_genome.fitness_score:.3f}")
        
        # Create new population
        new_population = []
        
        # Elitism: preserve top performers
        new_population.extend(self.population[:self.elite_count])
        logger.info(f"Preserving {self.elite_count} elite genomes")
        
        # Generate offspring
        while len(new_population) < self.population_size:
            parent1, parent2 = self.select_parents()
            offspring = self.crossover(parent1, parent2)
            offspring = await self.mutate(offspring)
            new_population.append(offspring)
        
        self.current_generation += 1
        logger.info(
            f"Generation {self.current_generation} complete: "
            f"avg_fitness={sum(g.fitness_score for g in new_population) / len(new_population):.3f}, "
            f"best_fitness={new_population[0].fitness_score:.3f}"
        )
        
        return new_population
    
    def _clone_genome(self, genome: EvolutionGenome) -> EvolutionGenome:
        """Create a deep copy of a genome."""
        return EvolutionGenome(
            agent_id=uuid4(),
            system_prompt=genome.system_prompt,
            temperature=genome.temperature,
            capabilities=genome.capabilities.copy(),
            hyperparameters=genome.hyperparameters.copy(),
            fitness_score=genome.fitness_score,
            generation=genome.generation,
        )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get evolution engine statistics.
        
        Returns:
            Dictionary with evolution stats
        """
        avg_fitness = 0.0
        if self.population:
            avg_fitness = sum(g.fitness_score for g in self.population) / len(self.population)

        return {
            "current_generation": self.current_generation,
            "population_size": len(self.population),
            "best_fitness": self.best_genome.fitness_score if self.best_genome else 0.0,
            "avg_population_fitness": avg_fitness,
            "active_agents": len(self.population),
        }



# ============================================================================
# Singleton Instance
# ============================================================================

evolution_engine = EvolutionEngine()
