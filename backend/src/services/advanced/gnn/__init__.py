"""
Graph Neural Networks Package

Advanced GNN implementations for knowledge graph reasoning, link prediction,
and multi-hop query answering.

Architecture:
- Node embeddings: TransE, DistMult, ComplEx
- Graph convolutions: GCN, GAT (Graph Attention Networks)
- Link prediction: Scoring functions with negative sampling
- Multi-hop reasoning: Path-based inference
"""

from .gnn_service import GNNService, EmbeddingQuality
from .node_embedder import NodeEmbedder, EmbeddingMethod
from .graph_convolution import GraphConvolution, ConvolutionType
from . link_predictor import LinkPredictor, ScoringFunction


# Placeholder Stub for MultiHopReasoner (not yet fully implemented)
class MultiHopReasoner:
    """Placeholder stub for multi-hop reasoning - will be fully implemented later."""
    
    async def find_related_entities(self, seed_entities: list, max_hops: int, top_k: int) -> list:
        """Find related entities using multi-hop reasoning."""
        # Stub implementation - returns empty list
        return []
    
    async def identify_gaps(self, query: str, current_knowledge: list) -> list:
        """Identify knowledge gaps."""
        # Stub implementation - returns empty list
        return []


# Create global instances for convenience
multi_hop_reasoner = MultiHopReasoner()
kg_embedder = NodeEmbedder()  # Alias for knowledge graph embedding


# Alias for backwards compatibility
KnowledgeGraphEmbedder = NodeEmbedder


__all__ = [
    "GNNService",
    "EmbeddingQuality",
    "NodeEmbedder",
    "EmbeddingMethod",
    "GraphConvolution",
    "ConvolutionType",
    "LinkPredictor",
    "ScoringFunction",
    "MultiHopReasoner",
    "multi_hop_reasoner",
    "kg_embedder",
    "KnowledgeGraphEmbedder",
]
