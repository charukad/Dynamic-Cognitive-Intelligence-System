"""
Oneiroi Scenario Generator

Generates training scenarios for dream cycles.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4
import random

from src.core import get_logger

logger = get_logger(__name__)


@dataclass
class ScenarioConfig:
    """Configuration for scenario generation"""
    counterfactual_variations: int = 3
    edge_case_difficulty_min: float = 0.7
    edge_case_difficulty_max: float = 0.95
    failure_replay_count: int = 5


class ScenarioGenerator:
    """
    Generates dream scenarios for agent training.
    
    Types:
    - Counterfactual: "What if I had chosen differently?"
   - Edge cases: Rare but critical situations
    - Failure replay: Re-experience failures with hindsight
    - Hybrid: Combine elements from different experiences
    """
    
    def __init__(self, config: Optional[ScenarioConfig] = None):
        self.config = config or ScenarioConfig()
    
    def generate_counterfactual(
        self,
        experience: Dict[str, Any],
        modification_type: Literal["strategy", "context", "parameters"] = "strategy"
    ) -> Dict[str, Any]:
        """
        Generate counterfactual scenario from experience.
        
        Creates "what-if" scenarios by modifying one aspect of
        a past experience.
        
        Args:
            experience: Base experience
            modification_type: What to modify
            
        Returns:
            Counterfactual scenario
        """
        scenario = {
            "id": str(uuid4()),
            "type": "counterfactual",
            "base_experience_id": experience.get("id"),
            "modification_type": modification_type,
            "context": experience.get("context", {}).copy(),
            "difficulty": experience.get("difficulty", 0.5),
        }
        
        # Apply modification based on type
        if modification_type == "strategy":
            scenario["variation"] = self._generate_alternative_strategy(
                experience.get("strategy", "default")
            )
        elif modification_type == "context":
            scenario["context"] = self._modify_context(scenario["context"])
        elif modification_type == "parameters":
            scenario["parameters"] = self._modify_parameters(
                experience.get("parameters", {})
            )
        
        logger.debug(f"Generated counterfactual scenario: {scenario['id']}")
        return scenario
    
    def generate_edge_cases(
        self,
        domain: str,
        count: int = 5,
        difficulty_range: Optional[tuple[float, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate challenging edge case scenarios.
        
        Edge cases test agent's ability to handle rare situations.
        
        Args:
            domain: Problem domain
            count: Number of edge cases to generate
            difficulty_range: Min and max difficulty (0.0-1.0)
            
        Returns:
            List of edge case scenarios
        """
        if difficulty_range is None:
            difficulty_range = (
                self.config.edge_case_difficulty_min,
                self.config.edge_case_difficulty_max
            )
        
        scenarios = []
        
        # Edge case categories
        edge_case_types = [
            "boundary_condition",
            "null_handling",
            "constraint_violation",
            "race_condition",
            "resource_exhaustion"
        ]
        
        for i in range(count):
            edge_type = random.choice(edge_case_types)
            difficulty = random.uniform(*difficulty_range)
            
            scenario = {
                "id": str(uuid4()),
                "type": "edge_case",
                "domain": domain,
                "edge_type": edge_type,
                "difficulty": difficulty,
                "context": self._generate_edge_case_context(edge_type, domain),
                "expected_challenges": self._get_expected_challenges(edge_type)
            }
            
            scenarios.append(scenario)
        
        logger.info(f"Generated {count} edge case scenarios for domain: {domain}")
        return scenarios
    
    def generate_failure_replay(
        self,
        failed_experiences: List[Dict[str, Any]],
        include_solution: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate scenarios that replay past failures.
        
        Allows agent to re-experience failures with knowledge of
        what went wrong and how to fix it.
        
        Args:
            failed_experiences: Past failures
            include_solution: Whether to include known solution
            
        Returns:
            Failure replay scenarios
        """
        scenarios = []
        
        # Take most impactful failures
        sorted_failures = sorted(
            failed_experiences,
            key=lambda x: abs(x.get("reward", 0) - 1.0),
            reverse=True
        )[:self.config.failure_replay_count]
        
        for failure in sorted_failures:
            scenario = {
                "id": str(uuid4()),
                "type": "failure_replay",
                "base_experience_id": failure.get("id"),
                "original_outcome": failure.get("reward", 0),
                "context": failure.get("context", {}).copy(),
                "difficulty": 0.6,  # Moderate, since agent knows what failed
            }
            
            if include_solution:
                scenario["hints"] = self._extract_failure_lessons(failure)
                scenario["optimal_strategy"] = self._derive_optimal_strategy(failure)
            
            scenarios.append(scenario)
        
        logger.info(f"Generated {len(scenarios)} failure replay scenarios")
        return scenarios
    
    def generate_hybrid(
        self,
        experiences: List[Dict[str, Any]],
        combination_size: int = 2
    ) -> Dict[str, Any]:
        """
        Generate hybrid scenario by combining elements from multiple experiences.
        
        Tests agent's ability to transfer knowledge across contexts.
        
        Args:
            experiences: Experiences to combine
            combination_size: Number of experiences to merge
            
        Returns:
            Hybrid scenario
        """
        if len(experiences) < combination_size:
            logger.warning("Not enough experiences for hybrid scenario")
            return self.generate_edge_cases("general", 1)[0]
        
        selected = random.sample(experiences, combination_size)
        
        scenario = {
            "id": str(uuid4()),
            "type": "hybrid",
            "source_experience_ids": [e.get("id") for e in selected],
            "context": {},
            "difficulty": 0.75,  # Higher due to novel combination
        }
        
        # Merge contexts
        for exp in selected:
            scenario["context"].update(exp.get("context", {}))
        
        # Combine challenges
        scenario["combined_challenges"] = list(set(
            challenge
            for exp in selected
            for challenge in exp.get("challenges", [])
        ))
        
        logger.debug(f"Generated hybrid scenario from {combination_size} experiences")
        return scenario
    
    def sample_from_distribution(
        self,
        experiences: List[Dict[str, Any]],
        strategy: Literal["uniform", "importance", "failure"] = "importance",
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Sample experiences for replay using different strategies.
        
        Args:
            experiences: All experiences
            strategy: Sampling strategy
            count: Number to sample
            
        Returns:
            Sampled experiences
        """
        if len(experiences) <= count:
            return experiences
        
        if strategy == "uniform":
            return random.sample(experiences, count)
        
        elif strategy == "importance":
            # Sample proportional to how much was learned
            weights = [
                abs(exp.get("reward", 0.5) - 0.5) + 0.1  # Deviation from average
                for exp in experiences
            ]
            return random.choices(experiences, weights=weights, k=count)
        
        elif strategy == "failure":
            # Focus on failures
            failures = [e for e in experiences if e.get("reward", 1.0) < 0.5]
            if len(failures) >= count:
                return random.sample(failures, count)
            else:
                # Backfill with low-reward experiences
                low_reward = sorted(experiences, key=lambda x: x.get("reward", 1.0))
                return low_reward[:count]
        
        return random.sample(experiences, count)
    
    # Helper methods
    
    def _generate_alternative_strategy(self, current_strategy: str) -> str:
        """Generate alternative to current strategy"""
        alternatives = {
            "greedy": "exploration",
            "exploration": "balanced",
            "balanced": "conservative",
            "conservative": "aggressive",
            "default": "optimized"
        }
        return alternatives.get(current_strategy, "alternative")
    
    def _modify_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Modify context for counterfactual"""
        modified = context.copy()
        # Add small variations
        if "temperature" in modified:
            modified["temperature"] = min(2.0, modified["temperature"] * 1.2)
        return modified
    
    def _modify_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Modify parameters for counterfactual"""
        modified = parameters.copy()
        # Vary parameters slightly
        for key, value in modified.items():
            if isinstance(value, (int, float)):
                modified[key] = value * random.uniform(0.8, 1.2)
        return modified
    
    def _generate_edge_case_context(
        self,
        edge_type: str,
        domain: str
    ) -> Dict[str, Any]:
        """Generate context for edge case"""
        contexts = {
            "boundary_condition": {"at_limit": True, "value": "max"},
            "null_handling": {"missing_data": True, "null_fields": ["input"]},
            "constraint_violation": {"constraint_broken": "time_limit"},
            "race_condition": {"concurrent_access": True},
            "resource_exhaustion": {"memory_pressure": "high"}
        }
        return contexts.get(edge_type, {"domain": domain})
    
    def _get_expected_challenges(self, edge_type: str) -> List[str]:
        """Get challenges for edge case type"""
        challenges = {
            "boundary_condition": ["overflow", "underflow", "limits"],
            "null_handling": ["missing_data", "validation"],
            "constraint_violation": ["time_limits", "resource_limits"],
            "race_condition": ["synchronization", "atomicity"],
            "resource_exhaustion": ["memory", "timeout"]
        }
        return challenges.get(edge_type, ["general"])
    
    def _extract_failure_lessons(
        self,
        failure: Dict[str, Any]
    ) -> List[str]:
        """Extract lessons from failure"""
        return [
            "Verify assumptions before proceeding",
            "Check edge cases thoroughly",
            "Validate inputs comprehensively"
        ]
    
    def _derive_optimal_strategy(
        self,
        failure: Dict[str, Any]
    ) -> str:
        """Derive optimal strategy to avoid failure"""
        return "Use systematic validation approach"


# Global instance
scenario_generator = ScenarioGenerator()
