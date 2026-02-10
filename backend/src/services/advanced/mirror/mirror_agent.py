"""
Mirror Protocol - Agent Self-Reflection and Metacognition

Enables agents to:
- Analyze their own reasoning processes
- Critique their own decisions
- Identify knowledge gaps
- Calibrate confidence levels
- Improve through self-reflection
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from src.core import get_logger

logger = get_logger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class ReflectionType(Enum):
    """Types of self-reflection."""
    REASONING_ANALYSIS = "reasoning_analysis"
    CONFIDENCE_CALIBRATION = "confidence_calibration"
    ERROR_ANALYSIS = "error_analysis"
    KNOWLEDGE_GAP = "knowledge_gap"
    STRATEGY_CRITIQUE = "strategy_critique"


@dataclass
class ReasoningTrace:
    """Trace of reasoning steps."""
    
    id: UUID
    task_description: str
    steps: List[Dict[str, Any]]
    final_conclusion: str
    confidence: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'task_description': self.task_description,
            'steps': self.steps,
            'final_conclusion': self.final_conclusion,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class SelfCritique:
    """Agent's self-critique of its reasoning."""
    
    id: UUID
    trace_id: UUID
    critique_type: ReflectionType
    identified_issues: List[str]
    suggested_improvements: List[str]
    confidence_adjustment: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'trace_id': str(self.trace_id),
            'critique_type': self.critique_type.value,
            'identified_issues': self.identified_issues,
            'suggested_improvements': self.suggested_improvements,
            'confidence_adjustment': self.confidence_adjustment,
            'timestamp': self.timestamp.isoformat(),
        }


# ============================================================================
# Mirror Agent - Self-Reflection System
# ============================================================================

class MirrorAgent:
    """
    Metacognitive agent for self-reflection.
    
    The Mirror Agent analyzes another agent's reasoning and provides
    critical feedback, identifying weaknesses and suggesting improvements.
    """
    
    def __init__(self, agent_id: UUID):
        """
        Initialize Mirror Agent.
        
        Args:
            agent_id: ID of the agent being reflected upon
        """
        self.agent_id = agent_id
        self.reflection_history: List[SelfCritique] = []
        
        logger.info(f"Initialized MirrorAgent for agent {agent_id}")
    
    def analyze_reasoning(self, trace: ReasoningTrace) -> SelfCritique:
        """
        Analyze reasoning trace and provide critique.
        
        Args:
            trace: Reasoning trace to analyze
            
        Returns:
            Self-critique with identified issues
        """
        issues = []
        improvements = []
        confidence_adjustment = 0.0
        
        # Check for logical inconsistencies
        if self._detect_contradictions(trace.steps):
            issues.append("Logical contradictions detected in reasoning chain")
            improvements.append("Review premises and ensure logical consistency")
            confidence_adjustment -= 0.2
        
        # Check for knowledge gaps
        gaps = self._identify_knowledge_gaps(trace.steps)
        if gaps:
            issues.extend([f"Missing knowledge: {gap}" for gap in gaps])
            improvements.append("Seek additional information before concluding")
            confidence_adjustment -= 0.15
        
        # Check for overconfidence
        if trace.confidence > 0.9 and len(trace.steps) < 3:
            issues.append("Insufficient reasoning depth for high confidence")
            improvements.append("Perform more thorough analysis before high-confidence claims")
            confidence_adjustment -= 0.25
        
        # Check for underconfidence
        if trace.confidence < 0.5 and self._has_strong_evidence(trace.steps):
            issues.append("Underconfident despite strong evidence")
            improvements.append("Trust the reasoning when evidence is clear")
            confidence_adjustment += 0.15
        
        critique = SelfCritique(
            id=uuid4(),
            trace_id=trace.id,
            critique_type=ReflectionType.REASONING_ANALYSIS,
            identified_issues=issues if issues else ["No major issues detected"],
            suggested_improvements=improvements if improvements else ["Reasoning appears sound"],
            confidence_adjustment=confidence_adjustment,
            timestamp=datetime.now(),
        )
        
        self.reflection_history.append(critique)
        
        logger.info(
            f"Analyzed reasoning trace {trace.id}: "
            f"{len(issues)} issues, adjustment={confidence_adjustment:.2f}"
        )
        
        return critique
    
    def calibrate_confidence(
        self,
        predicted_confidence: float,
        actual_outcome: bool,
    ) -> float:
        """
        Calibrate confidence based on actual outcomes.
        
        Args:
            predicted_confidence: Original confidence level
            actual_outcome: Whether prediction was correct
            
        Returns:
            Calibrated confidence multiplier
        """
        # If high confidence and correct, reinforce
        if predicted_confidence > 0.8 and actual_outcome:
            return 1.1
        
        # If high confidence but wrong, penalize heavily
        if predicted_confidence > 0.8 and not actual_outcome:
            return 0.6
        
        # If low confidence but correct, boost
        if predicted_confidence < 0.5 and actual_outcome:
            return 1.2
        
        # If low confidence and wrong, slight penalty
        if predicted_confidence < 0.5 and not actual_outcome:
            return 0.9
        
        # Moderate confidence
        return 1.0 if actual_outcome else 0.85
    
    def identify_knowledge_gaps(self, task: str) -> List[str]:
        """
        Identify what the agent doesn't know about a task.
        
        Args:
            task: Task description
            
        Returns:
            List of identified knowledge gaps
        """
        gaps = []
        
        # Simple keyword-based gap detection (can be enhanced with NLP)
        uncertainty_indicators = [
            'unclear', 'unsure', 'maybe', 'possibly',
            'not certain', 'unknown', 'don\'t know'
        ]
        
        task_lower = task.lower()
        for indicator in uncertainty_indicators:
            if indicator in task_lower:
                gaps.append(f"Uncertainty detected: '{indicator}'")
        
        # Check for complex domain-specific terms that might need clarification
        complex_terms = self._extract_complex_terms(task)
        if complex_terms:
            gaps.append(f"Complex terms requiring verification: {', '.join(complex_terms)}")
        
        return gaps
    
    def generate_improvement_plan(self) -> Dict[str, Any]:
        """
        Generate improvement plan based on reflection history.
        
        Returns:
            Improvement recommendations
        """
        if not self.reflection_history:
            return {
                'status': 'insufficient_data',
                'message': 'Need more reflection data for improvement plan',
            }
        
        # Aggregate issues across all reflections
        all_issues = []
        all_improvements = []
        avg_confidence_adj = 0.0
        
        for critique in self.reflection_history:
            all_issues.extend(critique.identified_issues)
            all_improvements.extend(critique.suggested_improvements)
            avg_confidence_adj += critique.confidence_adjustment
        
        avg_confidence_adj /= len(self.reflection_history)
        
        # Find most common issues
        issue_counts: Dict[str, int] = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'status': 'ready',
            'total_reflections': len(self.reflection_history),
            'avg_confidence_adjustment': avg_confidence_adj,
            'top_recurring_issues': [issue for issue, count in top_issues],
            'recommended_actions': list(set(all_improvements))[:10],
            'overall_assessment': self._assess_performance(avg_confidence_adj),
        }
    
    # Private helper methods
    
    def _detect_contradictions(self, steps: List[Dict[str, Any]]) -> bool:
        """Detect logical contradictions in reasoning steps."""
        # Simplified contradiction detection
        statements = [step.get('reasoning', '') for step in steps]
        
        # Look for negation patterns
        for i, stmt1 in enumerate(statements):
            for stmt2 in statements[i+1:]:
                if self._are_contradictory(stmt1, stmt2):
                    return True
        
        return False
    
    def _are_contradictory(self, stmt1: str, stmt2: str) -> bool:
        """Check if two statements contradict each other."""
        # Simple negation check (can be enhanced with semantic analysis)
        negation_words = ['not', 'no', 'never', 'cannot', 'isn\'t', 'aren\'t']
        
        stmt1_lower = stmt1.lower()
        stmt2_lower = stmt2.lower()
        
        # Check if one has negation and they're otherwise similar
        stmt1_has_neg = any(neg in stmt1_lower for neg in negation_words)
        stmt2_has_neg = any(neg in stmt2_lower for neg in negation_words)
        
        if stmt1_has_neg != stmt2_has_neg:
            # Remove negation words and check similarity
            stmt1_clean = stmt1_lower
            stmt2_clean = stmt2_lower
            for neg in negation_words:
                stmt1_clean = stmt1_clean.replace(neg, '')
                stmt2_clean = stmt2_clean.replace(neg, '')
            
            # Simple word overlap check
            words1 = set(stmt1_clean.split())
            words2 = set(stmt2_clean.split())
            overlap = len(words1 & words2) / max(len(words1), len(words2), 1)
            
            return overlap > 0.5
        
        return False
    
    def _identify_knowledge_gaps(self, steps: List[Dict[str, Any]]) -> List[str]:
        """Identify knowledge gaps in reasoning."""
        gaps = []
        
        for step in steps:
            reasoning = step.get('reasoning', '').lower()
            
            # Look for uncertainty markers
            if any(marker in reasoning for marker in ['assume', 'guess', 'estimate', 'approximately']):
                gaps.append(step.get('step_name', 'Unknown step'))
        
        return gaps
    
    def _has_strong_evidence(self, steps: List[Dict[str, Any]]) -> bool:
        """Check if reasoning has strong supporting evidence."""
        evidence_count = 0
        
        for step in steps:
            reasoning = step.get('reasoning', '').lower()
            
            # Look for evidence indicators
            if any(ind in reasoning for ind in ['because', 'therefore', 'thus', 'evidence', 'proven']):
                evidence_count += 1
        
        return evidence_count >= len(steps) * 0.6  # At least 60% of steps have evidence
    
    def _extract_complex_terms(self, text: str) -> List[str]:
        """Extract potentially complex technical terms."""
        words = text.split()
        complex_terms = []
        
        for word in words:
            # Simple heuristic: long words or capitalized technical terms
            if len(word) > 12 or (word[0].isupper() and len(word) > 6):
                complex_terms.append(word)
        
        return complex_terms[:5]  # Limit to top 5
    
    def _assess_performance(self, avg_conf_adj: float) -> str:
        """Assess overall performance based on confidence adjustments."""
        if avg_conf_adj > 0.1:
            return "Agent is underconfident - consider being more assertive with strong evidence"
        elif avg_conf_adj < -0.1:
            return "Agent is overconfident - more thorough analysis needed"
        else:
            return "Agent confidence is well-calibrated"


# ============================================================================
# Singleton Instance
# ============================================================================

# Create default mirror agent instance
default_mirror_agent = MirrorAgent(agent_id=UUID('00000000-0000-0000-0000-000000000000'))
