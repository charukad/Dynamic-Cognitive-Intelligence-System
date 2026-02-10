"""
GNN Service - Main orchestrator for graph neural network operations

Unified interface for:
- Training node embeddings on knowledge graphs
- Performing graph convolutions
- Predicting missing links
- Multi-hop reasoning and query answering
- Embedding quality assessment

Architecture: Facade pattern + Dependency Injection
Performance: Async operations, caching, batch processing
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import logging

from .node_embedder import (
    NodeEmbedder,
    Triple,
    EmbeddingMethod,
    EmbeddingConfig
)
from .graph_convolution import (
    GraphConvolution,
    GraphStructure,
    ConvolutionType
)
from .link_predictor import (
    LinkPredictor,
    LinkPrediction,
    ScoringFunction,
    PredictionMetrics
)

logger = logging.getLogger(__name__)


class EmbeddingQuality(Enum):
    """Embedding quality levels"""
    EXCELLENT = "excellent"  # MRR > 0.5
    GOOD = "good"  # MRR > 0.3
    FAIR = "fair"  # MRR > 0.15
    POOR = "poor"  # MRR <= 0.15


@dataclass
class GNNModel:
    """
    Trained GNN model with embeddings and metadata.
    
    Centralized model state for serialization and versioning.
    """
    model_id: str
    embedding_method: EmbeddingMethod
    convolution_type: Optional[ConvolutionType]
    embedding_dim: int
    num_entities: int
    num_relations: int
    training_loss: float
    epochs_trained: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    quality: Optional[EmbeddingQuality] = None
    
    # Embeddings (not serialized by default)
    _embedder: Optional[NodeEmbedder] = field(default=None, repr=False)
    _convolution: Optional[GraphConvolution] = field(default=None, repr=False)
    _predictor: Optional[LinkPredictor] = field(default=None, repr=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize model metadata (excludes large embeddings)"""
        return {
            'model_id': self.model_id,
            'embedding_method': self.embedding_method.value,
            'convolution_type': self.convolution_type.value if self.convolution_type else None,
            'embedding_dim': self.embedding_dim,
            'num_entities': self.num_entities,
            'num_relations': self.num_relations,
            'training_loss': round(self.training_loss, 4),
            'epochs_trained': self.epochs_trained,
            'created_at': self.created_at.isoformat(),
            'quality': self.quality.value if self.quality else None,
        }


class GNNService:
    """
    High-level GNN service for knowledge graph operations.
    
    Features:
    - Train embeddings with automatic quality assessment
    - Apply graph convolutions for feature learning
    - Predict missing links with confidence scores
    - Multi-hop reasoning for complex queries
    - Model versioning and management
    
    Usage:
        service = GNNService()
        model_id = await service.train_embeddings(triples, method=EmbeddingMethod.COMPLEX)
        predictions = await service.predict_link(model_id, 'Python', 'used_for')
    """
    
    def __init__(self):
        """Initialize GNN service"""
        self._models: Dict[str, GNNModel] = {}
        logger.info("GNN Service initialized")
    
    async def train_embeddings(
        self,
        model_id: str,
        triples: List[Dict[str, str]],
        embedding_method: EmbeddingMethod = EmbeddingMethod.COMPLEX,
        config: Optional[EmbeddingConfig] = None
    ) -> Dict[str, Any]:
        """
        Train node embeddings on knowledge graph triples.
        
        Args:
            model_id: Unique identifier for model
            triples: List of dicts with 'head', 'relation', 'tail' keys
            embedding_method: Algorithm to use
            config: Training configuration
        
        Returns:
            Training results with metrics
        """
        # Validate inputs
        if not triples:
            raise ValueError("Cannot train on empty triple set")
        
        if model_id in self._models:
            raise ValueError(f"Model '{model_id}' already exists")
        
        # Convert to Triple objects
        triple_objects = [
            Triple(head=t['head'], relation=t['relation'], tail=t['tail'])
            for t in triples
        ]
        
        # Initialize embedder
        embedder = NodeEmbedder(method=embedding_method)
        
        # Train
        config = config or EmbeddingConfig()
        
        logger.info(
            f"Training {embedding_method.value} embeddings for model '{model_id}': "
            f"{len(triple_objects)} triples, dim={config.embedding_dim}"
        )
        
        training_results = embedder.train(triple_objects, config)
        
        # Create predictor for quality assessment
        predictor = LinkPredictor(
            scoring_function=ScoringFunction(embedding_method.value)
        )
        predictor.set_embeddings(
            embedder.algorithm.entity_embeddings,
            embedder.algorithm.relation_embeddings
        )
        predictor.add_known_triples([
            (t.head, t.relation, t.tail) for t in triple_objects
        ])
        
        # Assess embedding quality (sample-based for speed)
        quality = await self._assess_quality(predictor, triple_objects)
        
        # Create model
        model = GNNModel(
            model_id=model_id,
            embedding_method=embedding_method,
            convolution_type=None,
            embedding_dim=config.embedding_dim,
            num_entities=training_results['num_entities'],
            num_relations=training_results['num_relations'],
            training_loss=training_results['final_loss'],
            epochs_trained=training_results['epochs_trained'],
            quality=quality,
            _embedder=embedder,
            _predictor=predictor
        )
        
        self._models[model_id] = model
        
        logger.info(
            f"Model '{model_id}' trained: {model.num_entities} entities, "
            f"quality={quality.value}"
        )
        
        return {
            'model_id': model_id,
            **training_results,
            'quality': quality.value,
        }
    
    async def apply_convolution(
        self,
        model_id: str,
        graph_edges: List[Tuple[str, str]],
        convolution_type: ConvolutionType = ConvolutionType.GAT,
        layer_dims: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Apply graph convolution to learn enhanced features.
        
        Args:
            model_id: Model identifier
            graph_edges: Graph structure (source, target) pairs
            convolution_type: GCN or GAT
            layer_dims: Layer dimensions [input, hidden, output]
        
        Returns:
            Convolution results
        """
        model = self._get_model(model_id)
        
        # Build graph structure
        node_features = model._embedder.algorithm.entity_embeddings.copy()
        
        graph = GraphStructure(
            edges=graph_edges,
            node_features=node_features,
            num_nodes=len(node_features),
            num_edges=len(graph_edges)
        )
        
        # Initialize convolution
        if layer_dims is None:
            dim = model.embedding_dim
            layer_dims = [dim, dim, dim]
        
        convolution = GraphConvolution(
            convolution_type=convolution_type,
            layer_dims=layer_dims
        )
        
        # Forward pass
        enhanced_features = convolution.forward(graph, node_features)
        
        # Update model embeddings
        model._embedder.algorithm.entity_embeddings = enhanced_features
        model.convolution_type = convolution_type
        model._convolution = convolution
        
        logger.info(
            f"Applied {convolution_type.value} convolution to model '{model_id}': "
            f"{len(layer_dims)} layers"
        )
        
        return {
            'model_id': model_id,
            'convolution_type': convolution_type.value,
            'num_layers': len(layer_dims),
            'layer_dims': layer_dims,
            'nodes_processed': len(enhanced_features),
        }
    
    async def predict_link(
        self,
        model_id: str,
        head: str,
        relation: str,
        top_k: int = 10,
        filter_known: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Predict missing tail entities for (head, relation, ?).
        
        Args:
            model_id: Model identifier
            head: Head entity
            relation: Relation type
            top_k: Number of predictions
            filter_known: Filter known triples
        
        Returns:
            List of predictions with scores
        """
        model = self._get_model(model_id)
        
        predictions = model._predictor.predict_tail(
            head, relation, top_k, filter_known
        )
        
        return [
            {
                'tail': p.tail,
                'score': round(p.score, 4),
                'rank': p.rank,
            }
            for p in predictions
        ]
    
    async def predict_head(
        self,
        model_id: str,
        relation: str,
        tail: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Predict missing head entities for (?, relation, tail)"""
        model = self._get_model(model_id)
        
        predictions = model._predictor.predict_head(relation, tail, top_k)
        
        return [
            {
                'head': p.head,
                'score': round(p.score, 4),
                'rank': p.rank,
            }
            for p in predictions
        ]
    
    async def predict_relation(
        self,
        model_id: str,
        head: str,
        tail: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Predict relation for (head, ?, tail)"""
        model = self._get_model(model_id)
        
        predictions = model._predictor.predict_relation(head, tail, top_k)
        
        return [
            {
                'relation': rel,
                'score': round(score, 4),
            }
            for rel, score in predictions
        ]
    
    async def multi_hop_reasoning(
        self,
        model_id: str,
        start_entity: str,
        relation_path: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform multi-hop reasoning via path composition.
        
        Example:
            start: "Python"
            path: ["created_by", "works_at"]
            result: Organizations employing Python creators
        """
        model = self._get_model(model_id)
        
        results = model._predictor.multi_hop_reasoning(
            start_entity, relation_path, top_k
        )
        
        return [
            {
                'entity': entity,
                'score': round(score, 4),
                'path_length': len(relation_path),
            }
            for entity, score in results
        ]
    
    async def find_similar_entities(
        self,
        model_id: str,
        entity: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Find most similar entities using cosine similarity"""
        model = self._get_model(model_id)
        
        similar = model._embedder.find_similar_entities(entity, top_k)
        
        return [
            {
                'entity': ent,
                'similarity': round(sim, 4),
            }
            for ent, sim in similar
        ]
    
    async def get_embedding(
        self,
        model_id: str,
        entity: str
    ) -> Optional[List[float]]:
        """Get embedding vector for entity"""
        model = self._get_model(model_id)
        
        embedding = model._embedder.get_embedding(entity)
        
        if embedding is not None:
            # Convert complex to real if needed
            import numpy as np
            if np.iscomplexobj(embedding):
                embedding = np.real(embedding)
            
            return embedding.tolist()
        
        return None
    
    async def evaluate_model(
        self,
        model_id: str,
        test_triples: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Evaluate model on test set.
        
        Returns comprehensive metrics.
        """
        model = self._get_model(model_id)
        
        test_triple_tuples = [
            (t['head'], t['relation'], t['tail']) for t in test_triples
        ]
        
        metrics = model._predictor.evaluate(test_triple_tuples, filter_known=True)
        
        return metrics.to_dict()
    
    async def get_model(self, model_id: str) -> Dict[str, Any]:
        """Get model metadata"""
        model = self._get_model(model_id)
        return model.to_dict()
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List all trained models"""
        return [model.to_dict() for model in self._models.values()]
    
    async def delete_model(self, model_id: str) -> bool:
        """Delete trained model"""
        if model_id in self._models:
            del self._models[model_id]
            logger.info(f"Deleted model '{model_id}'")
            return True
        return False
    
    def _get_model(self, model_id: str) -> GNNModel:
        """Get model or raise error"""
        if model_id not in self._models:
            raise ValueError(f"Model '{model_id}' not found")
        return self._models[model_id]
    
    async def _assess_quality(
        self,
        predictor: LinkPredictor,
        triples: List[Triple],
        sample_size: int = 100
    ) -> EmbeddingQuality:
        """
        Assess embedding quality via sample-based evaluation.
        
        Uses MRR (Mean Reciprocal Rank) as quality indicator.
        """
        import numpy as np
        
        # Sample triples for efficiency
        sample = triples[:min(sample_size, len(triples))]
        
        sample_tuples = [(t.head, t.relation, t.tail) for t in sample]
        metrics = predictor.evaluate(sample_tuples, filter_known=True)
        
        mrr = metrics.mean_reciprocal_rank
        
        # Quality thresholds
        if mrr > 0.5:
            return EmbeddingQuality.EXCELLENT
        elif mrr > 0.3:
            return EmbeddingQuality.GOOD
        elif mrr > 0.15:
            return EmbeddingQuality.FAIR
        else:
            return EmbeddingQuality.POOR


# Singleton instance
gnn_service = GNNService()
