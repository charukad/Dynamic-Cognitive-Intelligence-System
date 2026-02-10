"""Memory services for DCIS.

Provides access to:
- Episodic memory (conversation history)
- Semantic memory (knowledge storage)
- Procedural memory (successful patterns)
- Working memory (session context)
- Embedding pipeline (RAG)
- Knowledge graph (Neo4j)
"""

from src.infrastructure.database import chroma_client, neo4j_client
from src.infrastructure.llm import vllm_client
from src.services.memory.embedding_pipeline import (
    EmbeddingPipeline,
    embedding_pipeline,
    set_embedding_pipeline,
)
from src.services.memory.episodic_memory import EpisodicMemoryService
from src.services.memory.knowledge_graph import (
    KnowledgeGraphService,
    knowledge_graph_service,
)
from src.services.memory.procedural_memory import ProceduralMemoryService
from src.services.memory.semantic_memory import SemanticMemoryService
from src.services.memory.working_memory import WorkingMemoryService

# Initialize embedding pipeline instance
_pipeline = EmbeddingPipeline(
    chromadb_client=chroma_client,
    llm_client=vllm_client,
    chunk_size=500,
    chunk_overlap=50,
)
set_embedding_pipeline(_pipeline)

# Initialize memory services
episodic_memory_service = EpisodicMemoryService()
semantic_memory_service = SemanticMemoryService()
procedural_memory_service = ProceduralMemoryService()
working_memory_service = WorkingMemoryService()

__all__ = [
    "embedding_pipeline",
    "episodic_memory_service",
    "semantic_memory_service",
    "procedural_memory_service",
    "working_memory_service",
    "knowledge_graph_service",
    "EmbeddingPipeline",
    "EpisodicMemoryService",
    "SemanticMemoryService",
    "ProceduralMemoryService",
    "WorkingMemoryService",
    "KnowledgeGraphService",
]
