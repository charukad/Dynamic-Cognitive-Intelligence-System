"""
Meta-Learning System - Learning to Learn

Implements meta-learning capabilities:
- Strategy database for successful task patterns
- Few-shot learning from past successes
- Transfer learning between similar tasks
- Automated prompt optimization
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from src.core import get_logger

logger = get_logger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class SuccessfulStrategy:
    """A proven successful strategy for a task pattern."""
    
    id: UUID
    task_pattern: str
    strategy_description: str
    agent_configuration: Dict[str, Any]
    success_metrics: Dict[str, float]
    usage_count: int = 0
    avg_success_rate: float = 0.0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'task_pattern': self.task_pattern,
            'strategy_description': self.strategy_description,
            'agent_configuration': self.agent_configuration,
            'success_metrics': self.success_metrics,
            'usage_count': self.usage_count,
            'avg_success_rate': self.avg_success_rate,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class TaskPattern:
    """Pattern extracted from a task."""
    
    domain: str
    complexity: str
    required_capabilities: List[str]
    keywords: List[str]
    
    def similarity(self, other: 'TaskPattern') -> float:
        """
        Calculate similarity with another pattern.
        
        Args:
            other: Pattern to compare with
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        score = 0.0
        
        # Domain match
        if self.domain == other.domain:
            score += 0.3
        
        # Complexity match
        if self.complexity == other.complexity:
            score += 0.2
        
        # Capability overlap
        cap_overlap = len(set(self.required_capabilities) & set(other.required_capabilities))
        cap_total = len(set(self.required_capabilities) | set(other.required_capabilities))
        if cap_total > 0:
            score += 0.3 * (cap_overlap / cap_total)
        
        # Keyword overlap
        kw_overlap = len(set(self.keywords) & set(other.keywords))
        kw_total = len(set(self.keywords) | set(other.keywords))
        if kw_total > 0:
            score += 0.2 * (kw_overlap / kw_total)
        
        return min(1.0, score)


# ============================================================================
# Meta-Learner
# ============================================================================

class MetaLearner:
    """
    Meta-learning system for task-to-strategy mapping.
    
    Learns patterns from successful task completions and applies
    them to new similar tasks.
    """
    
    def __init__(self):
        """Initialize meta-learner."""
        self.strategy_database: Dict[str, SuccessfulStrategy] = {}
        self.pattern_index: Dict[str, List[str]] = {}  # domain -> strategy IDs
        
        logger.info("Initialized Meta-Learner")
    
    def extract_pattern(self, task_description: str) -> TaskPattern:
        """
        Extract task pattern from description.
        
        Args:
            task_description: Task description text
            
        Returns:
            Extracted pattern
        """
        # Simple keyword-based extraction (can be enhanced with NLP)
        description_lower = task_description.lower()
        
        # Determine domain
        domain = 'general'
        if any(kw in description_lower for kw in ['code', 'program', 'develop', 'implement']):
            domain = 'coding'
        elif any(kw in description_lower for kw in ['analyze', 'data', 'statistics']):
            domain = 'analysis'
        elif any(kw in description_lower for kw in ['research', 'find', 'investigate']):
            domain = 'research'
        elif any(kw in description_lower for kw in ['creative', 'design', 'brainstorm']):
            domain = 'creative'
        
        # Determine complexity
        complexity = 'medium'
        if len(task_description.split()) < 10:
            complexity = 'simple'
        elif len(task_description.split()) > 30:
            complexity = 'complex'
        
        # Extract capabilities
        capabilities = []
        if 'analyze' in description_lower:
            capabilities.append('analysis')
        if 'create' in description_lower or 'generate' in description_lower:
            capabilities.append('generation')
        if 'optimize' in description_lower:
            capabilities.append('optimization')
        if 'explain' in description_lower:
            capabilities.append('explanation')
        
        # Extract keywords
        keywords = [
            word for word in description_lower.split()
            if len(word) > 4 and word.isalpha()
        ][:10]  # Top 10 keywords
        
        return TaskPattern(
            domain=domain,
            complexity=complexity,
            required_capabilities=capabilities,
            keywords=keywords,
        )
    
    def store_success(
        self,
        task_description: str,
        agent_config: Dict[str, Any],
        success_metrics: Dict[str, float],
    ) -> SuccessfulStrategy:
        """
        Store a successful task completion.
        
        Args:
            task_description: Task description
            agent_config: Agent configuration that succeeded
            success_metrics: Performance metrics
            
        Returns:
            Created strategy
        """
        pattern = self.extract_pattern(task_description)
        
        strategy = SuccessfulStrategy(
            id=uuid4(),
            task_pattern=f"{pattern.domain}:{pattern.complexity}",
            strategy_description=f"Successful strategy for {pattern.domain} tasks",
            agent_configuration=agent_config,
            success_metrics=success_metrics,
            usage_count=1,
            avg_success_rate=success_metrics.get('success_rate', 0.8),
        )
        
        self.strategy_database[str(strategy.id)] = strategy
        
        # Index by domain
        if pattern.domain not in self.pattern_index:
            self.pattern_index[pattern.domain] = []
        self.pattern_index[pattern.domain].append(str(strategy.id))
        
        logger.info(f"Stored successful strategy: {strategy.task_pattern}")
        return strategy
    
    def retrieve_strategy(
        self,
        task_description: str,
        top_k: int = 3,
    ) -> List[SuccessfulStrategy]:
        """
        Retrieve similar successful strategies.
        
        Args:
            task_description: New task description
            top_k: Number of strategies to return
            
        Returns:
            List of relevant strategies
        """
        pattern = self.extract_pattern(task_description)
        
        # Get candidate strategies from same domain
        candidate_ids = self.pattern_index.get(pattern.domain, [])
        
        if not candidate_ids:
            logger.info(f"No strategies found for domain: {pattern.domain}")
            return []
        
        candidates = [self.strategy_database[sid] for sid in candidate_ids]
        
        # Sort by success rate and usage
        candidates.sort(
            key=lambda s: (s.avg_success_rate * 0.7 + min(s.usage_count / 100, 1.0) * 0.3),
            reverse=True
        )
        
        strategies = candidates[:top_k]
        
        logger.info(
            f"Retrieved {len(strategies)} strategies for pattern: {pattern.task_pattern}"
        )
        
        return strategies
    
    def apply_strategy(
        self,
        strategy: SuccessfulStrategy,
        current_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Apply learned strategy to current configuration.
        
        Args:
            strategy: Strategy to apply
            current_config: Current agent configuration
            
        Returns:
            Enhanced configuration
        """
        # Merge strategy configuration with current
        enhanced_config = {**current_config}
        
        # Apply temperature adjustment
        if 'temperature' in strategy.agent_configuration:
            enhanced_config['temperature'] = strategy.agent_configuration['temperature']
        
        # Add proven capabilities
        if 'capabilities' in strategy.agent_configuration:
            current_caps = set(enhanced_config.get('capabilities', []))
            strategy_caps = set(strategy.agent_configuration['capabilities'])
            enhanced_config['capabilities'] = list(current_caps | strategy_caps)
        
        # Update system prompt with successful patterns
        if 'system_prompt_suffix' in strategy.agent_configuration:
            enhanced_config['system_prompt'] = (
                current_config.get('system_prompt', '') + 
                ' ' + 
                strategy.agent_configuration['system_prompt_suffix']
            )
        
        strategy.usage_count += 1
        
        logger.info(f"Applied strategy {strategy.id} to configuration")
        return enhanced_config
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get meta-learning statistics."""
        return {
            'total_strategies': len(self.strategy_database),
            'domains': list(self.pattern_index.keys()),
            'avg_success_rate': (
                sum(s.avg_success_rate for s in self.strategy_database.values()) / 
                len(self.strategy_database) if self.strategy_database else 0.0
            ),
            'most_used': max(
                self.strategy_database.values(),
                key=lambda s: s.usage_count,
                default=None
            ).to_dict() if self.strategy_database else None,
        }


# ============================================================================
# Singleton Instance
# ============================================================================

meta_learner = MetaLearner()
