"""
Development endpoint for seeding memory data in the running server.

This endpoint populates the in-memory repository with sample data
for testing the Memory Inspector visualization.
"""

from fastapi import APIRouter

from src.core import get_logger
from src.services.memory import (
    episodic_memory_service,
    semantic_memory_service,
)

router = APIRouter(prefix="/dev", tags=["development"])
logger = get_logger(__name__)


SAMPLE_EPISODIC = [
    ("Discussed machine learning fundamentals with user", 0.8, ["ml", "education"], "session_1"),
   ("Explained neural network architectures", 0.9, ["neural-networks", "deep-learning"], "session_1"),
    ("Helped debug PyTorch training loop", 0.7, ["pytorch", "debugging"], "session_2"),
    ("Discussed transformer attention mechanisms", 0.9, ["transformers", "attention"], "session_2"),
    ("User asked about deploying ML models", 0.7, ["mlops", "deployment"], "session_3"),
    ("Explained reinforcement learning basics", 0.7, ["rl", "algorithms"], "session_3"),
    ("Discussed latest LLM developments", 0.9, ["llm", "gpt"], "session_1"),
    ("Helped implement vector database", 0.7, ["embeddings", "vector-db"], "session_2"),
]

SAMPLE_SEMANTIC = [
    ("Neural networks are composed of interconnected layers of nodes", 0.9, ["neural-networks", "definition"]),
    ("Transformers use self-attention mechanisms for processing sequences", 0.9, ["transformers", "attention"]),
    ("Gradient descent minimizes loss functions through iterative optimization", 0.9, ["optimization", "algorithms"]),
    ("CNNs are specialized for processing grid-like data such as images", 0.8, ["cnn", "computer-vision"]),
    ("Transfer learning leverages pre-trained models for related tasks", 0.8, ["transfer-learning", "concepts"]),
]


@router.post("/seed-memory")
async def seed_memory_data():
    """
    Seed the in-memory repository with sample data.
    
    **Dev-only endpoint** - Populates memory for testing visualizations.
    """
    try:
        # Seed episodic memories
        episodic_count = 0
        for content, importance, tags, session in SAMPLE_EPISODIC:
            await episodic_memory_service.store_memory(
                content=content,
                session_id=session,
                importance_score=importance,
                tags=tags,
            )
            episodic_count += 1
        
        # Seed semantic memories
        semantic_count = 0
        for content, importance, tags in SAMPLE_SEMANTIC:
            await semantic_memory_service.store_knowledge(
                knowledge=content,
                importance_score=importance,
                tags=tags,
            )
            semantic_count += 1
        
        logger.info(f"Seeded {episodic_count} episodic and {semantic_count} semantic memories")
        
        return {
            "status": "success",
            "episodic_seeded": episodic_count,
            "semantic_seeded": semantic_count,
            "message": "Memory data seeded successfully. Visit /dashboard?tab=memory to view."
        }
        
    except Exception as e:
        logger.error(f"Failed to seed memory: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }
