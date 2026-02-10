"""Active Learning for uncertainty reduction and clarification."""

import math
from typing import Any, Dict, List, Optional, Tuple

from src.core import get_logger
from src.infrastructure.llm import vllm_client

logger = get_logger(__name__)


class ActiveLearner:
    """
    Active Learning implementation for uncertainty-driven queries.
    
    Identifies uncertain responses and generates clarifying questions
    to improve accuracy.
    """

    def __init__(
        self,
        uncertainty_threshold: float = 0.6,
        max_clarifications: int = 3,
    ) -> None:
        """
        Initialize Active Learner.
        
        Args:
            uncertainty_threshold: Threshold for requesting clarification
            max_clarifications: Maximum clarifying questions
        """
        self.uncertainty_threshold = uncertainty_threshold
        self.max_clarifications = max_clarifications

    async def analyze_uncertainty(
        self,
        query: str,
        response: str,
    ) -> Dict[str, Any]:
        """
        Analyze uncertainty in a response.
        
        Args:
            query: Original query
            response: Response to analyze
            
        Returns:
            Uncertainty analysis
        """
        logger.info("Analyzing response uncertainty")

        # Calculate uncertainty score
        uncertainty_score = await self._calculate_uncertainty(query, response)
        
        # Identify uncertain aspects
        uncertain_aspects = await self._identify_uncertain_aspects(
            query=query,
            response=response,
        )

        # Generate clarifying questions if needed
        clarifying_questions = []
        needs_clarification = uncertainty_score > self.uncertainty_threshold
        
        if needs_clarification:
            clarifying_questions = await self._generate_clarifying_questions(
                query=query,
                response=response,
                uncertain_aspects=uncertain_aspects,
            )

        return {
            "uncertainty_score": uncertainty_score,
            "needs_clarification": needs_clarification,
            "uncertain_aspects": uncertain_aspects,
            "clarifying_questions": clarifying_questions,
            "confidence": 1.0 - uncertainty_score,
        }

    async def refine_with_feedback(
        self,
        query: str,
        response: str,
        user_feedback: str,
    ) -> str:
        """
        Refine response based on user feedback.
        
        Args:
            query: Original query
            response: Original response
            user_feedback: User's clarification or correction
            
        Returns:
            Refined response
        """
        logger.info("Refining response with user feedback")

        prompt = f"""Refine the response based on user feedback.

Original Query: {query}

Original Response: {response}

User Feedback: {user_feedback}

Provide a refined, improved response that incorporates the feedback:"""

        try:
            refined = await vllm_client.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=800,
            )
            
            return refined.strip()
            
        except Exception as e:
            logger.error(f"Failed to refine response: {e}")
            return response

    async def _calculate_uncertainty(
        self,
        query: str,
        response: str,
    ) -> float:
        """
        Calculate uncertainty score for a response.
        
        Args:
            query: Query
            response: Response
            
        Returns:
            Uncertainty score (0.0-1.0)
        """
        # Use multiple uncertainty indicators
        indicators = await self._get_uncertainty_indicators(query, response)
        
        # Combine indicators
        scores = []
        
        # Hedging language indicator
        hedging_words = ["maybe", "might", "possibly", "perhaps", "unclear", "uncertain", "not sure"]
        hedging_count = sum(1 for word in hedging_words if word in response.lower())
        hedging_score = min(hedging_count / 3.0, 1.0)
        scores.append(hedging_score)
        
        # Length indicator (very short responses might be uncertain)
        length_score = max(0.0, 1.0 - len(response.split()) / 100.0)
        scores.append(length_score * 0.3)  # Lower weight
        
        # Missing information indicator
        if "don't know" in response.lower() or "cannot" in response.lower():
            scores.append(0.8)
        
        # Question marks (asking back indicates uncertainty)
        question_count = response.count("?")
        question_score = min(question_count / 2.0, 1.0)
        scores.append(question_score * 0.7)
        
        # Average all indicators
        if scores:
            uncertainty = sum(scores) / len(scores)
        else:
            uncertainty = 0.3  # Default moderate uncertainty
        
        logger.debug(f"Calculated uncertainty: {uncertainty:.2f}")
        
        return min(max(uncertainty, 0.0), 1.0)

    async def _get_uncertainty_indicators(
        self,
        query: str,
        response: str,
    ) -> Dict[str, float]:
        """
        Get various uncertainty indicators.
        
        Args:
            query: Query
            response: Response
            
        Returns:
            Uncertainty indicators
        """
        return {
            "hedging": 0.0,  # Placeholder
            "length": 0.0,
            "specificity": 0.0,
        }

    async def _identify_uncertain_aspects(
        self,
        query: str,
        response: str,
    ) -> List[str]:
        """
        Identify specific uncertain aspects of the response.
        
        Args:
            query: Query
            response: Response
            
        Returns:
            List of uncertain aspects
        """
        prompt = f"""Identify any uncertain or ambiguous aspects in this response.

Query: {query}

Response: {response}

List specific aspects that seem uncertain, ambiguous, or require clarification. If the response is clear and confident, respond with "No uncertain aspects."

Uncertain aspects:"""

        try:
            result = await vllm_client.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=200,
            )
            
            if "no uncertain" in result.lower():
                return []
            
            # Parse aspects
            aspects = []
            for line in result.strip().split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    aspect = line.lstrip('0123456789.-) ').strip()
                    if aspect:
                        aspects.append(aspect)
            
            return aspects
            
        except Exception as e:
            logger.error(f"Failed to identify uncertain aspects: {e}")
            return []

    async def _generate_clarifying_questions(
        self,
        query: str,
        response: str,
        uncertain_aspects: List[str],
    ) -> List[str]:
        """
        Generate clarifying questions to reduce uncertainty.
        
        Args:
            query: Query
            response: Response
            uncertain_aspects: Identified uncertain aspects
            
        Returns:
            List of clarifying questions
        """
        aspects_text = "\n".join([f"- {aspect}" for aspect in uncertain_aspects])
        
        prompt = f"""Generate clarifying questions to help improve this uncertain response.

Original Query: {query}

Response: {response}

Uncertain Aspects:
{aspects_text}

Generate {self.max_clarifications} specific clarifying questions that would help provide a more accurate and complete answer. Return only the questions, one per line.

Questions:"""

        try:
            result = await vllm_client.generate(
                prompt=prompt,
                temperature=0.4,
                max_tokens=300,
            )
            
            questions = []
            for line in result.strip().split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or '?' in line):
                    question = line.lstrip('0123456789.-) ').strip()
                    if question and question.endswith('?'):
                        questions.append(question)
            
            return questions[:self.max_clarifications]
            
        except Exception as e:
            logger.error(f"Failed to generate clarifying questions: {e}")
            return []

    async def entropy_based_sampling(
        self,
        candidates: List[Dict[str, Any]],
        k: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Select most uncertain candidates using entropy.
        
        Args:
            candidates: Candidate items with probabilities
            k: Number to select
            
        Returns:
            Top k uncertain candidates
        """
        def calculate_entropy(probs: List[float]) -> float:
            """Calculate Shannon entropy."""
            entropy = 0.0
            for p in probs:
                if p > 0:
                    entropy -= p * math.log2(p)
            return entropy
        
        # Calculate entropy for each candidate
        scored_candidates = []
        for candidate in candidates:
            probs = candidate.get("probabilities", [0.5, 0.5])
            entropy = calculate_entropy(probs)
            scored_candidates.append({
                **candidate,
                "entropy": entropy,
            })
        
        # Sort by entropy (descending)
        scored_candidates.sort(key=lambda x: x.get("entropy", 0.0), reverse=True)
        
        return scored_candidates[:k]


# Singleton instance
active_learner = ActiveLearner()
