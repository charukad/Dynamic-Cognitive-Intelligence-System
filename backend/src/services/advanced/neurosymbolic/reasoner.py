"""
Neurosymbolic Reasoning Engine

Hybrid system combining:
- Neural networks (pattern recognition, embeddings)
- Symbolic logic (rules, constraints, formal reasoning)

Enables:
- Logical inference with learned patterns
- Rule extraction from neural models
- Constraint-based reasoning with uncertainty
- Interpretable AI decisions
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from src.core import get_logger

logger = get_logger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class LogicalOperator(Enum):
    """Logical operators for symbolic reasoning."""
    AND = "and"
    OR = "or"
    NOT = "not"
    IMPLIES = "implies"
    IFF = "iff"  # if and only if


@dataclass
class SymbolicRule:
    """Logical rule in symbolic form."""
    
    id: UUID
    name: str
    premises: List[str]  # Antecedents
    conclusion: str  # Consequent
    confidence: float  # Neural-derived confidence
    operator: LogicalOperator = LogicalOperator.IMPLIES
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'name': self.name,
            'premises': self.premises,
            'conclusion': self.conclusion,
            'confidence': self.confidence,
            'operator': self.operator.value,
        }
    
    def evaluate(self, facts: Set[str]) -> Optional[str]:
        """
        Evaluate rule against known facts.
        
        Args:
            facts: Set of known true facts
            
        Returns:
            Conclusion if rule fires, None otherwise
        """
        if self.operator == LogicalOperator.IMPLIES:
            # If all premises are true, conclusion follows
            if all(premise in facts for premise in self.premises):
                return self.conclusion
        
        elif self.operator == LogicalOperator.AND:
            # All premises must be true
            if all(premise in facts for premise in self.premises):
                return self.conclusion
        
        elif self.operator == LogicalOperator.OR:
            # At least one premise must be true
            if any(premise in facts for premise in self.premises):
                return self.conclusion
        
        return None


@dataclass
class NeuralPattern:
    """Pattern learned from neural network."""
    
    id: UUID
    pattern_type: str
    features: Dict[str, float]
    confidence: float
    instances_seen: int
   
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'pattern_type': self.pattern_type,
            'features': self.features,
            'confidence': self.confidence,
            'instances_seen': self.instances_seen,
        }


# ============================================================================
# Neurosymbolic Reasoner
# ============================================================================

class NeurosymbolicReasoner:
    """
    Hybrid reasoning engine combining neural and symbolic AI.
    
    Architecture:
    1. Neural layer: Pattern recognition and embedding
    2. Symbolic layer: Logical inference and constraints
    3. Fusion layer: Combine neural confidence with logical certainty
    """
    
    def __init__(self):
        """Initialize neurosymbolic reasoner."""
        self.symbolic_rules: Dict[str, SymbolicRule] = {}
        self.neural_patterns: Dict[str, NeuralPattern] = {}
        self.fact_base: Set[str] = set()
        
        # Initialize with some basic rules
        self._initialize_default_rules()
        
        logger.info("Initialized NeurosymbolicReasoner")
    
    def _initialize_default_rules(self):
        """Initialize with common-sense reasoning rules."""
        # Transitive property
        self.add_rule(SymbolicRule(
            id=uuid4(),
            name="transitivity",
            premises=["A implies B", "B implies C"],
            conclusion="A implies C",
            confidence=1.0,
        ))
        
        # Modus ponens
        self.add_rule(SymbolicRule(
            id=uuid4(),
            name="modus_ponens",
            premises=["P", "P implies Q"],
            conclusion="Q",
            confidence=1.0,
        ))
    
    def add_rule(self, rule: SymbolicRule):
        """Add symbolic rule to knowledge base."""
        self.symbolic_rules[str(rule.id)] = rule
        logger.info(f"Added rule: {rule.name}")
    
    def add_fact(self, fact: str):
        """Add fact to fact base."""
        self.fact_base.add(fact)
        logger.debug(f"Added fact: {fact}")
    
    def add_neural_pattern(self, pattern: NeuralPattern):
        """Add learned neural pattern."""
        self.neural_patterns[str(pattern.id)] = pattern
        logger.info(f"Added neural pattern: {pattern.pattern_type}")
    
    def forward_chain(self, max_iterations: int = 10) -> Set[str]:
        """
        Perform forward chaining inference.
        
        Args:
            max_iterations: Maximum inference iterations
            
        Returns:
            Set of derived facts
        """
        derived_facts = set(self.fact_base)
        iteration = 0
        
        while iteration < max_iterations:
            new_facts = set()
            
            # Try to fire each rule
            for rule in self.symbolic_rules.values():
                conclusion = rule.evaluate(derived_facts)
                if conclusion and conclusion not in derived_facts:
                    new_facts.add(conclusion)
                    logger.debug(f"Rule '{rule.name}' fired → {conclusion}")
            
            # No new facts derived, stop
            if not new_facts:
                break
            
            derived_facts.update(new_facts)
            iteration += 1
        
        logger.info(f"Forward chaining completed: {len(derived_facts)} total facts")
        return derived_facts
    
    def backward_chain(self, goal: str, max_depth: int = 5) -> Tuple[bool, List[str]]:
        """
        Perform backward chaining to prove goal.
        
        Args:
            goal: Goal fact to prove
            max_depth: Maximum proof depth
            
        Returns:
            Tuple of (proved, proof_steps)
        """
        return self._backward_chain_recursive(goal, set(), max_depth, [])
    
    def _backward_chain_recursive(
        self,
        goal: str,
        visited: Set[str],
        depth: int,
        proof: List[str],
    ) -> Tuple[bool, List[str]]:
        """Recursive backward chaining."""
        # Base case: goal is a known fact
        if goal in self.fact_base:
            proof.append(f"✓ {goal} (fact)")
            return True, proof
        
        # Base case: max depth reached
        if depth == 0:
            proof.append(f"✗ {goal} (max depth)")
            return False, proof
        
        # Avoid cycles
        if goal in visited:
            return False, proof
        
        visited.add(goal)
        
        # Try to find a rule that concludes the goal
        for rule in self.symbolic_rules.values():
            if rule.conclusion == goal:
                proof.append(f"→ Trying rule '{rule.name}': {' ∧ '.join(rule.premises)} ⇒ {goal}")
                
                # Try to prove all premises
                all_proved = True
                for premise in rule.premises:
                    proved, proof = self._backward_chain_recursive(
                        premise, visited.copy(), depth - 1, proof
                    )
                    if not proved:
                        all_proved = False
                        break
                
                if all_proved:
                    proof.append(f"✓ {goal} (via {rule.name})")
                    return True, proof
        
        proof.append(f"✗ {goal} (no proof found)")
        return False, proof
    
    def extract_rules_from_patterns(self) -> List[SymbolicRule]:
        """
        Extract symbolic rules from learned neural patterns.
        
        Returns:
            List of extracted rules
        """
        extracted_rules = []
        
        for pattern in self.neural_patterns.values():
            # Convert high-confidence patterns to rules
            if pattern.confidence > 0.8:
                # Extract top features as premises
                sorted_features = sorted(
                    pattern.features.items(),
                    key=lambda x: abs(x[1]),
                    reverse=True
                )[:3]
                
                premises = [f"{feat}={val:.2f}" for feat, val in sorted_features]
                conclusion = f"pattern_{pattern.pattern_type}"
                
                rule = SymbolicRule(
                    id=uuid4(),
                    name=f"neural_rule_{pattern.pattern_type}",
                    premises=premises,
                    conclusion=conclusion,
                    confidence=pattern.confidence,
                )
                
                extracted_rules.append(rule)
                self.add_rule(rule)
        
        logger.info(f"Extracted {len(extracted_rules)} rules from neural patterns")
        return extracted_rules
    
    def hybrid_inference(
        self,
        query: str,
        neural_context: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Perform hybrid neural-symbolic inference.
        
        Args:
            query: Query to infer
            neural_context: Neural network outputs/embeddings
            
        Returns:
            Inference result with confidence
        """
        # Symbolic inference
        proved, proof = self.backward_chain(query)
        symbolic_confidence = 1.0 if proved else 0.0
        
        # Neural inference (if context provided)
        neural_confidence = 0.5
        if neural_context:
            # Find matching patterns
            matching_patterns = self._match_neural_patterns(neural_context)
            if matching_patterns:
                neural_confidence = max(p.confidence for p in matching_patterns)
        
        # Fusion: Combine symbolic and neural confidences
        # Weighted average favoring symbolic when available
        fusion_weight = 0.7 if proved else 0.3
        final_confidence = (
            fusion_weight * symbolic_confidence +
            (1 - fusion_weight) * neural_confidence
        )
        
        return {
            'query': query,
            'proved': proved,
            'confidence': final_confidence,
            'symbolic_confidence': symbolic_confidence,
            'neural_confidence': neural_confidence,
            'proof': proof,
            'method': 'hybrid',
        }
    
    def _match_neural_patterns(
        self,
        context: Dict[str, float],
    ) -> List[NeuralPattern]:
        """Find neural patterns matching context."""
        matches = []
        
        for pattern in self.neural_patterns.values():
            # Calculate similarity between context and pattern features
            similarity = self._calculate_similarity(context, pattern.features)
            if similarity > 0.7:
                matches.append(pattern)
        
        return matches
    
    def _calculate_similarity(
        self,
        dict1: Dict[str, float],
        dict2: Dict[str, float],
    ) -> float:
        """Calculate cosine similarity between feature dicts."""
        # Get common keys
        common_keys = set(dict1.keys()) & set(dict2.keys())
        if not common_keys:
            return 0.0
        
        # Dot product
        dot_product = sum(dict1[k] * dict2[k] for k in common_keys)
        
        # Magnitudes
        mag1 = sum(v ** 2 for v in dict1.values()) ** 0.5
        mag2 = sum(v ** 2 for v in dict2.values()) ** 0.5
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get reasoning engine statistics."""
        return {
            'total_rules': len(self.symbolic_rules),
            'total_patterns': len(self.neural_patterns),
            'total_facts': len(self.fact_base),
            'avg_rule_confidence': (
                sum(r.confidence for r in self.symbolic_rules.values()) /
                len(self.symbolic_rules) if self.symbolic_rules else 0.0
            ),
            'avg_pattern_confidence': (
                sum(p.confidence for p in self.neural_patterns.values()) /
                len(self.neural_patterns) if self.neural_patterns else 0.0
            ),
        }


# ============================================================================
# Singleton Instance
# ============================================================================

neurosymbolic_reasoner = NeurosymbolicReasoner()
