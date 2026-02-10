"""Chain-of-Verification (CoVe) for hallucination detection and correction."""

from typing import Any, Dict, List, Optional

from src.core import get_logger
from src.infrastructure.llm import vllm_client
from src.services.memory import episodic_memory_service

logger = get_logger(__name__)


class ChainOfVerification:
    """
    Chain-of-Verification (CoVe) implementation.
    
    Reduces hallucinations by:
    1. Generating verification questions
    2. Answering verification questions independently
    3. Detecting contradictions
    4. Revising original response
    """

    def __init__(self, max_revision_rounds: int = 2) -> None:
        """
        Initialize CoVe.
        
        Args:
            max_revision_rounds: Maximum revision iterations
        """
        self.max_revision_rounds = max_revision_rounds

    async def verify_response(
        self,
        query: str,
        response: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Verify a response using Chain-of-Verification.
        
        Args:
            query: Original query
            response: Response to verify
            session_id: Optional session ID
            
        Returns:
            Verification result with revised response
        """
        logger.info("Starting Chain-of-Verification")

        # Step 1: Generate verification questions
        verification_questions = await self._generate_verification_questions(
            query=query,
            response=response,
        )
        
        logger.info(f"Generated {len(verification_questions)} verification questions")

        # Step 2: Answer verification questions independently
        verification_answers = await self._answer_verification_questions(
            questions=verification_questions,
            original_query=query,
        )

        # Step 3: Detect contradictions
        contradictions = await self._detect_contradictions(
            original_response=response,
            verification_qa=verification_answers,
        )
        
        logger.info(f"Detected {len(contradictions)} contradictions")

        # Step 4: Revise if contradictions found
        revised_response = response
        revision_history = []
        
        if contradictions:
            for round_num in range(self.max_revision_rounds):
                logger.info(f"Revision round {round_num + 1}/{self.max_revision_rounds}")
                
                revised_response = await self._revise_response(
                    query=query,
                    original_response=revised_response,
                    contradictions=contradictions,
                    verification_qa=verification_answers,
                )
                
                revision_history.append({
                    "round": round_num + 1,
                    "response": revised_response,
                    "contradictions_addressed": len(contradictions),
                })
                
                # Check if contradictions resolved
                new_contradictions = await self._detect_contradictions(
                    original_response=revised_response,
                    verification_qa=verification_answers,
                )
                
                if not new_contradictions:
                    logger.info("All contradictions resolved")
                    break
                
                contradictions = new_contradictions

        # Store verification in memory
        if session_id:
            await episodic_memory_service.store_memory(
                content=f"CoVe verification: {len(contradictions)} contradictions, {len(revision_history)} revisions",
                session_id=session_id,
                tags=["cove", "verification"],
            )

        return {
            "original_response": response,
            "verification_questions": verification_questions,
            "verification_answers": verification_answers,
            "contradictions": contradictions,
            "revised_response": revised_response,
            "revision_history": revision_history,
            "improved": len(contradictions) > 0 and len(revision_history) > 0,
        }

    async def _generate_verification_questions(
        self,
        query: str,
        response: str,
    ) -> List[str]:
        """
        Generate verification questions about the response.
        
        Args:
            query: Original query
            response: Response to verify
            
        Returns:
            List of verification questions
        """
        prompt = f"""Given this query and response, generate 3-5 specific verification questions to check for factual accuracy and consistency.

Query: {query}

Response: {response}

Generate verification questions that:
1. Check specific claims made in the response
2. Test for internal consistency
3. Verify key facts or assumptions

Return ONLY the questions, one per line, numbered 1-5."""

        try:
            result = await vllm_client.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=300,
            )
            
            # Parse questions
            questions = []
            for line in result.strip().split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove numbering/bullets
                    question = line.lstrip('0123456789.-) ').strip()
                    if question:
                        questions.append(question)
            
            return questions[:5]  # Limit to 5 questions
            
        except Exception as e:
            logger.error(f"Failed to generate verification questions: {e}")
            return []

    async def _answer_verification_questions(
        self,
        questions: List[str],
        original_query: str,
    ) -> List[Dict[str, str]]:
        """
        Answer verification questions independently.
        
        Args:
            questions: Verification questions
            original_query: Original query for context
            
        Returns:
            List of Q&A pairs
        """
        qa_pairs = []
        
        for question in questions:
            prompt = f"""Answer this verification question based on factual knowledge. Be concise and specific.

Original context: {original_query}

Verification question: {question}

Answer:"""

            try:
                answer = await vllm_client.generate(
                    prompt=prompt,
                    temperature=0.2,
                    max_tokens=200,
                )
                
                qa_pairs.append({
                    "question": question,
                    "answer": answer.strip(),
                })
                
            except Exception as e:
                logger.error(f"Failed to answer verification question: {e}")
                qa_pairs.append({
                    "question": question,
                    "answer": f"[Error: {str(e)}]",
                })
        
        return qa_pairs

    async def _detect_contradictions(
        self,
        original_response: str,
        verification_qa: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        """
        Detect contradictions between response and verification answers.
        
        Args:
            original_response: Original response
            verification_qa: Verification Q&A pairs
            
        Returns:
            List of contradictions
        """
        contradictions = []
        
        # Format verification Q&A
        qa_text = "\n".join([
            f"Q: {qa['question']}\nA: {qa['answer']}"
            for qa in verification_qa
        ])
        
        prompt = f"""Compare the original response with the verification answers. Identify any contradictions or inconsistencies.

Original Response:
{original_response}

Verification Q&A:
{qa_text}

List any contradictions found. For each contradiction, state:
1. What the original response claimed
2. What the verification revealed
3. The specific inconsistency

If no contradictions, respond with "No contradictions found."

Contradictions:"""

        try:
            result = await vllm_client.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=400,
            )
            
            if "no contradictions" in result.lower():
                return []
            
            # Parse contradictions (simple line-based parsing)
            for line in result.strip().split('\n'):
                line = line.strip()
                if line and len(line) > 20:  # Meaningful content
                    contradictions.append({
                        "description": line,
                    })
            
        except Exception as e:
            logger.error(f"Failed to detect contradictions: {e}")
        
        return contradictions

    async def _revise_response(
        self,
        query: str,
        original_response: str,
        contradictions: List[Dict[str, str]],
        verification_qa: List[Dict[str, str]],
    ) -> str:
        """
        Revise response to address contradictions.
        
        Args:
            query: Original query
            original_response: Response to revise
            contradictions: Detected contradictions
            verification_qa: Verification Q&A
            
        Returns:
            Revised response
        """
        contradictions_text = "\n".join([
            f"- {c['description']}"
            for c in contradictions
        ])
        
        qa_text = "\n".join([
            f"Q: {qa['question']}\nA: {qa['answer']}"
            for qa in verification_qa
        ])
        
        prompt = f"""Revise the response to address the contradictions identified. Use the verification Q&A to ensure accuracy.

Original Query: {query}

Original Response:
{original_response}

Contradictions Found:
{contradictions_text}

Verification Q&A:
{qa_text}

Provide a revised, accurate response that addresses all contradictions:"""

        try:
            revised = await vllm_client.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=800,
            )
            
            return revised.strip()
            
        except Exception as e:
            logger.error(f"Failed to revise response: {e}")
            return original_response


# Singleton instance
chain_of_verification = ChainOfVerification()
