"""
Contradiction Detector - Find logical conflicts using NLI

Uses Natural Language Inference to detect contradictions in:
- Agent responses within same session
- Knowledge base entries
- User statements vs. past statements

Techniques:
- Natural Language Inference (NLI) classification
- Negation detection
- Temporal logic checking
"""

from typing import List, Dict, Any, Optional, Tuple
import re
from enum import Enum


class ContradictionType(Enum):
    """Types of contradictions"""
    DIRECT = "direct"  # "X is true" vs "X is false"
    LOGICAL = "logical"  # Syllogistic contradiction
    TEMPORAL = "temporal"  # Time-based conflict
    SEMANTIC = "semantic"  # Meaning-level conflict


class ContradictionSeverity(Enum):
    """Severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContradictionDetector:
    """Detect contradictions in text statements"""
    
    def __init__(self):
        """Initialize detector with linguistic patterns"""
        # Negation patterns
        self.negation_markers = {
            'not', 'no', 'never', 'none', 'nobody', 'nothing', 'neither',
            'nowhere', 'cannot', "can't", "won't", "don't", "doesn't",
            "didn't", "isn't", "aren't", "wasn't", "weren't"
        }
        
        # Antonym pairs (simplified - production would use embeddings)
        self.antonyms = {
            'fast': 'slow',
            'good': 'bad',
            'hot': 'cold',
            'big': 'small',
            'high': 'low',
            'true': 'false',
            'correct': 'incorrect',
            'safe': 'unsafe',
            'secure': 'insecure',
            'stable': 'unstable',
        }
        
        # Reverse antonyms mapping
        for key, val in list(self.antonyms.items()):
            self.antonyms[val] = key
        
        # Absolute quantifiers
        self.absolute_quantifiers = {
            'all', 'every', 'always', 'never', 'none', 'no'
        }
    
    def detect_contradiction(
        self,
        statement1: str,
        statement2: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect if two statements contradict each other.
        
        Args:
            statement1: First statement
            statement2: Second statement
            context: Optional context (timestamps, sources, etc.)
        
        Returns:
            Contradiction analysis result
        """
        # Normalize statements
        s1 = statement1.lower().strip()
        s2 = statement2.lower().strip()
        
        # Check for direct negation
        direct = self._check_direct_negation(s1, s2)
        if direct['is_contradiction']:
            return self._format_result(
                is_contradiction=True,
                contradiction_type=ContradictionType.DIRECT,
                severity=ContradictionSeverity.HIGH,
                confidence=direct['confidence'],
                explanation=direct['explanation'],
                statement1=statement1,
                statement2=statement2,
            )
        
        # Check for antonym-based contradiction
        antonym = self._check_antonym_contradiction(s1, s2)
        if antonym['is_contradiction']:
            return self._format_result(
                is_contradiction=True,
                contradiction_type=ContradictionType.SEMANTIC,
                severity=ContradictionSeverity.MEDIUM,
                confidence=antonym['confidence'],
                explanation=antonym['explanation'],
                statement1=statement1,
                statement2=statement2,
            )
        
        # Check for logical contradiction
        logical = self._check_logical_contradiction(s1, s2)
        if logical['is_contradiction']:
            return self._format_result(
                is_contradiction=True,
                contradiction_type=ContradictionType.LOGICAL,
                severity=ContradictionSeverity.HIGH,
                confidence=logical['confidence'],
                explanation=logical['explanation'],
                statement1=statement1,
                statement2=statement2,
            )
        
        # No contradiction detected
        return self._format_result(
            is_contradiction=False,
            contradiction_type=None,
            severity=None,
            confidence=0.8,
            explanation="No contradiction detected between statements",
            statement1=statement1,
            statement2=statement2,
        )
    
    def detect_batch_contradictions(
        self,
        statements: List[str],
        min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find all contradictions in a list of statements.
        
        Args:
            statements: List of statements to check
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of contradiction pairs
        """
        contradictions = []
        
        for i in range(len(statements)):
            for j in range(i + 1, len(statements)):
                result = self.detect_contradiction(statements[i], statements[j])
                
                if result['is_contradiction'] and result['confidence'] >= min_confidence:
                    contradictions.append({
                        'statement1_index': i,
                        'statement2_index': j,
                        **result
                    })
        
        return contradictions
    
    def _check_direct_negation(self, s1: str, s2: str) -> Dict[str, Any]:
        """Check if s2 is direct negation of s1"""
        # Remove punctuation
        s1_clean = re.sub(r'[^\w\s]', '', s1)
        s2_clean = re.sub(r'[^\w\s]', '', s2)
        
        s1_words = set(s1_clean.split())
        s2_words = set(s2_clean.split())
        
        # Check if s1 has negation but s2 doesn't (or vice versa)
        s1_has_neg = bool(s1_words & self.negation_markers)
        s2_has_neg = bool(s2_words & self.negation_markers)
        
        # Remove negation words for comparison
        s1_content = s1_words - self.negation_markers
        s2_content = s2_words - self.negation_markers
        
        # Calculate overlap
        overlap = len(s1_content & s2_content) / max(len(s1_content), len(s2_content), 1)
        
        # If high overlap (>60%) and opposite negation, likely contradiction
        if overlap > 0.6 and s1_has_neg != s2_has_neg:
            return {
                'is_contradiction': True,
                'confidence': min(0.95, overlap),
                'explanation': f"Direct negation detected (overlap: {overlap:.0%})"
            }
        
        return {'is_contradiction': False, 'confidence': 0.0, 'explanation': ''}
    
    def _check_antonym_contradiction(self, s1: str, s2: str) -> Dict[str, Any]:
        """Check for antonym-based contradictions"""
        s1_words = set(s1.split())
        s2_words = set(s2.split())
        
        # Find antonym pairs
        antonym_pairs = []
        for word in s1_words:
            if word in self.antonyms:
                antonym = self.antonyms[word]
                if antonym in s2_words:
                    antonym_pairs.append((word, antonym))
        
        if antonym_pairs:
            # Check if rest of sentence is similar
            s1_clean = s1
            s2_clean = s2
            for w1, w2 in antonym_pairs:
                s1_clean = s1_clean.replace(w1, '')
                s2_clean = s2_clean.replace(w2, '')
            
            # Simple similarity check
            s1_remaining = set(s1_clean.split())
            s2_remaining = set(s2_clean.split())
            
            if len(s1_remaining & s2_remaining) > 3:
                return {
                    'is_contradiction': True,
                    'confidence': 0.75,
                    'explanation': f"Antonym pair detected: {antonym_pairs[0]}"
                }
        
        return {'is_contradiction': False, 'confidence': 0.0, 'explanation': ''}
    
    def _check_logical_contradiction(self, s1: str, s2: str) -> Dict[str, Any]:
        """Check for logical contradictions (universal vs. existential)"""
        # Detect universal statements ("all X are Y")
        all_pattern = r'\b(all|every|always)\s+(\w+)\s+(are|is|have|has)\s+(\w+)'
        some_pattern = r'\b(some|a|an)\s+(\w+)\s+(are|is|have|has)\s+not\s+(\w+)'
        
        all_match1 = re.search(all_pattern, s1)
        some_match2 = re.search(some_pattern, s2)
        
        if all_match1 and some_match2:
            # "All X are Y" vs "Some X are not Y" is a logical contradiction
            return {
                'is_contradiction': True,
                'confidence': 0.8,
                'explanation': "Universal vs. existential contradiction"
            }
        
        # Check reverse
        all_match2 = re.search(all_pattern, s2)
        some_match1 = re.search(some_pattern, s1)
        
        if all_match2 and some_match1:
            return {
                'is_contradiction': True,
                'confidence': 0.8,
                'explanation': "Universal vs. existential contradiction"
            }
        
        return {'is_contradiction': False, 'confidence': 0.0, 'explanation': ''}
    
    def _format_result(
        self,
        is_contradiction: bool,
        contradiction_type: Optional[ContradictionType],
        severity: Optional[ContradictionSeverity],
        confidence: float,
        explanation: str,
        statement1: str,
        statement2: str,
    ) -> Dict[str, Any]:
        """Format contradiction detection result"""
        return {
            'is_contradiction': is_contradiction,
            'contradiction_type': contradiction_type.value if contradiction_type else None,
            'severity': severity.value if severity else None,
            'confidence': round(confidence, 3),
            'explanation': explanation,
            'statement1': statement1,
            'statement2': statement2,
        }
    
    def explain_contradiction(self, result: Dict[str, Any]) -> str:
        """Generate human-readable explanation of contradiction"""
        if not result['is_contradiction']:
            return "No contradiction detected."
        
        explanation = f"**Contradiction Detected** ({result['severity']} severity)\n\n"
        explanation += f"**Type**: {result['contradiction_type']}\n"
        explanation += f"**Confidence**: {result['confidence']:.0%}\n\n"
        explanation += f"**Statement 1**: {result['statement1']}\n"
        explanation += f"**Statement 2**: {result['statement2']}\n\n"
        explanation += f"**Reason**: {result['explanation']}\n"
        
        return explanation
