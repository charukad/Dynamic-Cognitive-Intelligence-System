#!/usr/bin/env python3
"""
Memory Data Seeding Script

Populates memory databases with realistic sample data for development and demo purposes.
Creates:
- Episodic memories (conversation-based)
- Semantic memories (knowledge facts)
- Knowledge graph nodes and relationships
"""

import asyncio
import random
from datetime import datetime, timedelta
from uuid import uuid4

# Add backend to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import get_logger, setup_logging
from src.services.memory import (
    episodic_memory_service,
    semantic_memory_service,
    knowledge_graph_service,
)

logger = get_logger(__name__)


# Sample data
EPISODIC_MEMORIES = [
    ("User asked about machine learning fundamentals", 0.8, ["machine-learning", "education"]),
    ("Discussed the difference between supervised and unsupervised learning", 0.7, ["machine-learning", "concepts"]),
    ("Explained neural network architecture basics", 0.9, ["neural-networks", "deep-learning"]),
    ("User inquired about training a sentiment analysis model", 0.6, ["nlp", "sentiment-analysis"]),
    ("Helped debug a PyTorch training loop issue", 0.7, ["pytorch", "debugging"]),
    ("Discussed transfer learning and pre-trained models", 0.8, ["transfer-learning", "optimization"]),
    ("Explained gradient descent and backpropagation", 0.9, ["optimization", "fundamentals"]),
    ("User asked for recommendations on ML frameworks", 0.5, ["frameworks", "tools"]),
    ("Compared TensorFlow and PyTorch features", 0.6, ["tensorflow", "pytorch"]),
    ("Discussed overfitting and regularization techniques", 0.8, ["overfitting", "regularization"]),
    ("Helped design a CNN architecture for image classification", 0.9, ["cnn", "computer-vision"]),
    ("Explained attention mechanisms in transformers", 0.9, ["transformers", "attention"]),
    ("User asked about deploying ML models to production", 0.7, ["mlops", "deployment"]),
    ("Discussed data preprocessing and feature engineering", 0.6, ["preprocessing", "features"]),
    ("Explained cross-validation and model evaluation metrics", 0.7, ["validation", "metrics"]),
    ("Helped optimize a model for inference speed", 0.8, ["optimization", "inference"]),
    ("Discussed ethical considerations in AI development", 0.8, ["ethics", "responsibility"]),
    ("User inquired about reinforcement learning basics", 0.7, ["reinforcement-learning", "rl"]),
    ("Explained Q-learning and policy gradients", 0.8, ["rl", "algorithms"]),
    ("Discussed few-shot learning and meta-learning", 0.7, ["few-shot", "meta-learning"]),
    ("User asked about the latest developments in LLMs", 0.9, ["llm", "gpt", "trends"]),
    ("Explained prompt engineering best practices", 0.8, ["prompt-engineering", "llm"]),
    ("Discussed RAG (Retrieval-Augmented Generation)", 0.9, ["rag", "retrieval"]),
    ("Helped implement a vector database for embeddings", 0.7, ["embeddings", "vector-db"]),
    ("User inquired about model compression techniques", 0.6, ["compression", "quantization"]),
    ("Explained knowledge distillation process", 0.7, ["distillation", "compression"]),
    ("Discussed multi-modal learning and CLIP", 0.8, ["multimodal", "clip"]),
    ("User asked about graph neural networks", 0.7, ["gnn", "graphs"]),
    ("Explained the architecture of GPT and transformer models", 0.9, ["gpt", "transformers"]),
    ("Discussed fine-tuning strategies for LLMs", 0.8, ["fine-tuning", "llm"]),
]

SEMANTIC_MEMORIES = [
    ("A neural network is composed of layers of interconnected nodes called neurons", 0.9, ["neural-networks", "definition"]),
    ("Gradient descent is an optimization algorithm used to minimize loss functions", 0.9, ["optimization", "algorithms"]),
    ("Convolutional Neural Networks (CNNs) are specialized for processing grid-like data such as images", 0.8, ["cnn", "computer-vision"]),
    ("Transformers use self-attention mechanisms to process sequential data", 0.9, ["transformers", "attention"]),
    ("Overfitting occurs when a model learns noise in the training data instead of underlying patterns", 0.8, ["overfitting", "concepts"]),
    ("Regularization techniques like L1 and L2 help prevent overfitting", 0.7, ["regularization", "techniques"]),
    ("Transfer learning leverages pre-trained models to solve related tasks", 0.8, ["transfer-learning", "concepts"]),
    ("Reinforcement Learning is about learning to make decisions through trial and error", 0.8, ["reinforcement-learning", "definition"]),
    ("Embeddings map discrete data like words into continuous vector spaces", 0.8, ["embeddings", "representation"]),
    ("BERT is a bidirectional transformer model for understanding language context", 0.9, ["bert", "nlp"]),
    ("GPT models are autoregressive transformers trained for text generation", 0.9, ["gpt", "generation"]),
    ("Attention mechanisms allow models to focus on relevant parts of the input", 0.9, ["attention", "mechanisms"]),
    ("Batch normalization normalizes layer inputs to stabilize training", 0.7, ["batch-norm", "techniques"]),
    ("Dropout randomly deactivates neurons during training to prevent overfitting", 0.7, ["dropout", "regularization"]),
    ("Cross-entropy loss is commonly used for classification tasks", 0.7, ["loss-functions", "classification"]),
    ("Adam optimizer combines momentum and adaptive learning rates", 0.7, ["optimizers", "adam"]),
    ("Recurrent Neural Networks (RNNs) process sequential data with loops in their architecture", 0.8, ["rnn", "sequential"]),
    ("LSTMs solve the vanishing gradient problem in standard RNNs", 0.8, ["lstm", "rnn"]),
    ("GANs consist of a generator and discriminator trained adversarially", 0.8, ["gan", "generative"]),
    ("Vector databases enable efficient similarity search using embeddings", 0.8, ["vector-db", "retrieval"]),
]

KNOWLEDGE_GRAPH_DATA = {
    "concepts": [
        ("Artificial Intelligence", "Domain", {"importance": 0.9}),
        ("Machine Learning", "Domain", {"importance": 0.9}),  
        ("Deep Learning", "Domain", {"importance": 0.9}),
        ("Neural Networks", "Model", {"importance": 0.9}),
        ("Transformers", "Architecture", {"importance": 0.9}),
        ("CNN", "Architecture", {"importance": 0.8}),
        ("RNN", "Architecture", {"importance": 0.8}),
        ("LSTM", "Architecture", {"importance": 0.8}),
        ("GPT", "Model", {"importance": 0.9}),
        ("BERT", "Model", {"importance": 0.9}),
        ("Attention Mechanism", "Technique", {"importance": 0.9}),
        ("Backpropagation", "Algorithm", {"importance": 0.9}),
        ("Gradient Descent", "Algorithm", {"importance": 0.9}),
        ("Adam Optimizer", "Algorithm", {"importance": 0.7}),
        ("Transfer Learning", "Technique", {"importance": 0.8}),
        ("Fine-tuning", "Technique", {"importance": 0.8}),
        ("Embeddings", "Representation", {"importance": 0.8}),
        ("Computer Vision", "Domain", {"importance": 0.8}),
        ("Natural Language Processing", "Domain", {"importance": 0.9}),
        ("Reinforcement Learning", "Domain", {"importance": 0.8}),
        ("Supervised Learning", "Paradigm", {"importance": 0.8}),
        ("Unsupervised Learning", "Paradigm", {"importance": 0.8}),
        ("Overfitting", "Problem", {"importance": 0.7}),
        ("Regularization", "Technique", {"importance": 0.7}),
        ("Dropout", "Technique", {"importance": 0.6}),
        ("Batch Normalization", "Technique", {"importance": 0.6}),
        ("PyTorch", "Framework", {"importance": 0.8}),
        ("TensorFlow", "Framework", {"importance": 0.8}),
        ("Vector Database", "Tool", {"importance": 0.7}),
        ("RAG", "Architecture", {"importance": 0.8}),
        ("LLM", "Model", {"importance": 0.9}),
        ("Prompt Engineering", "Technique", {"importance": 0.7}),
        ("Multi-modal Learning", "Domain", {"importance": 0.7}),
        ("Graph Neural Networks", "Architecture", {"importance": 0.7}),
        ("Knowledge Distillation", "Technique", {"importance": 0.6}),
    ],
    "relationships": [
        ("Machine Learning", "IS_PART_OF", "Artificial Intelligence"),
        ("Deep Learning", "IS_PART_OF", "Machine Learning"),
        ("Neural Networks", "IS_FOUNDATION_OF", "Deep Learning"),
        ("Transformers", "IS_TYPE_OF", "Neural Networks"),
        ("CNN", "IS_TYPE_OF", "Neural Networks"),
        ("RNN", "IS_TYPE_OF", "Neural Networks"),
        ("LSTM", "IS_TYPE_OF", "RNN"),
        ("GPT", "USES", "Transformers"),
        ("BERT", "USES", "Transformers"),
        ("Transformers", "USES", "Attention Mechanism"),
        ("Neural Networks", "TRAINED_WITH", "Backpropagation"),
        ("Backpropagation", "USES", "Gradient Descent"),
        ("Adam Optimizer", "IS_TYPE_OF", "Gradient Descent"),
        ("Transfer Learning", "APPLIES_TO", "Deep Learning"),
        ("Fine-tuning", "IS_TYPE_OF", "Transfer Learning"),
        ("Embeddings", "USED_IN", "Natural Language Processing"),
        ("CNN", "USED_IN", "Computer Vision"),
        ("Transformers", "USED_IN", "Natural Language Processing"),
        ("BERT", "GENERATES", "Embeddings"),
        ("GPT", "GENERATES", "Embeddings"),
        ("Regularization", "PREVENTS", "Overfitting"),
        ("Dropout", "IS_TYPE_OF", "Regularization"),
        ("Batch Normalization", "IS_TYPE_OF", "Regularization"),
        ("PyTorch", "IMPLEMENTS", "Neural Networks"),
        ("TensorFlow", "IMPLEMENTS", "Neural Networks"),
        ("Vector Database", "STORES", "Embeddings"),
        ("RAG", "USES", "Vector Database"),
        ("RAG", "USES", "LLM"),
        ("Prompt Engineering", "APPLIES_TO", "LLM"),
        ("LLM", "IS_TYPE_OF", "Transformers"),
        ("Multi-modal Learning", "IS_PART_OF", "Deep Learning"),
        ("Graph Neural Networks", "IS_TYPE_OF", "Neural Networks"),
        ("Knowledge Distillation", "IS_TYPE_OF", "Transfer Learning"),
        ("Supervised Learning", "IS_PART_OF", "Machine Learning"),
        ("Unsupervised Learning", "IS_PART_OF", "Machine Learning"),
        ("Reinforcement Learning", "IS_PART_OF", "Machine Learning"),
    ]
}


async def seed_episodic_memories():
    """Seed episodic memories with varied timestamps and sessions."""
    logger.info("Seeding episodic memories...")
    
    # Create 3 different sessions
    sessions = [f"session_{i}" for i in range(1, 4)]
    base_time = datetime.now() - timedelta(days=7)
    
    for i, (content, importance, tags) in enumerate(EPISODIC_MEMORIES):
        # Distribute memories across sessions
        session_id = sessions[i % len(sessions)]
        
        # Vary timestamps (spread over last 7 days)
        timestamp_offset = timedelta(hours=i * 2 + random.randint(0, 120))
        
        try:
            memory = await episodic_memory_service.store_memory(
                content=content,
                session_id=session_id,
                importance_score=importance,
                tags=tags,
            )
            logger.info(f"Created episodic memory {i+1}/{len(EPISODIC_MEMORIES)}: {memory.id}")
        except Exception as e:
            logger.error(f"Failed to create episodic memory '{content}': {e}")
    
    logger.info(f"✓ Seeded {len(EPISODIC_MEMORIES)} episodic memories")


async def seed_semantic_memories():
    """Seed semantic memories (factual knowledge)."""
    logger.info("Seeding semantic memories...")
    
    for i, (content, importance, tags) in enumerate(SEMANTIC_MEMORIES):
        try:
            memory = await semantic_memory_service.store_knowledge(
                knowledge=content,
                importance_score=importance,
                tags=tags,
            )
            logger.info(f"Created semantic memory {i+1}/{len(SEMANTIC_MEMORIES)}: {memory.id}")
        except Exception as e:
            logger.error(f"Failed to create semantic memory '{content}': {e}")
    
    logger.info(f"✓ Seeded {len(SEMANTIC_MEMORIES)} semantic memories")


async def seed_knowledge_graph():
    """Seed knowledge graph with concept nodes and relationships."""
    logger.info("Seeding knowledge graph...")
    
    # Create concept nodes
    concept_nodes = {}
    for i, (name, concept_type, properties) in enumerate(KNOWLEDGE_GRAPH_DATA["concepts"]):
        try:
            node = await knowledge_graph_service.add_concept(
                concept=name,
                concept_type=concept_type,
                properties=properties,
            )
            concept_nodes[name] = node
            logger.info(f"Created concept {i+1}/{len(KNOWLEDGE_GRAPH_DATA['concepts'])}: {name}")
        except Exception as e:
            logger.error(f"Failed to create concept '{name}': {e}")
    
    logger.info(f"✓ Seeded {len(concept_nodes)} knowledge graph concepts")
    
    # Create relationships
    relationships_created = 0
    for from_concept, rel_type, to_concept in KNOWLEDGE_GRAPH_DATA["relationships"]:
        try:
            from_node = concept_nodes.get(from_concept)
            to_node = concept_nodes.get(to_concept)
            
            if from_node and to_node and from_node.get("id") and to_node.get("id"):
                await knowledge_graph_service.add_relationship(
                    from_concept_id=from_node["id"],
                    to_concept_id=to_node["id"],
                    relationship_type=rel_type,
                )
                relationships_created += 1
                logger.info(f"Created relationship: {from_concept} -{rel_type}-> {to_concept}")
            else:
                logger.warning(f"Skipping relationship {from_concept} -> {to_concept}: nodes not found")
        except Exception as e:
            logger.error(f"Failed to create relationship '{from_concept} -> {to_concept}': {e}")
    
    logger.info(f"✓ Seeded {relationships_created} knowledge graph relationships")


async def main():
    """Main seeding function."""
    setup_logging()
    logger.info("=" * 80)
    logger.info("Starting Memory Data Seeding")
    logger.info("=" * 80)
    
    try:
        # Initialize database connections
        from src.core.lifecycle import lifecycle_manager
        await lifecycle_manager.startup()
        
        # Seed all memory types
        await seed_episodic_memories()
        await seed_semantic_memories()
        await seed_knowledge_graph()
        
        logger.info("=" * 80)
        logger.info("✓ Memory seeding completed successfully!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Seeding failed: {e}", exc_info=True)
        return 1
    finally:
        # Cleanup
        await lifecycle_manager.shutdown()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
