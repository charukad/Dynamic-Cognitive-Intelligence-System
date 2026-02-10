"""
Graph Neural Networks Tests

Comprehensive tests for GNN components:
- Node embeddings (TransE, DistMult, ComplEx)
- Graph convolutions (GCN, GAT)
- Link prediction
- Multi-hop reasoning
"""

import pytest
import numpy as np
from src.services.advanced.gnn import (
    NodeEmbedder,
    EmbeddingMethod,
    EmbeddingConfig,
    Triple,
    GraphConvolution,
    ConvolutionType,
    GraphStructure,
    LinkPredictor,
    ScoringFunction,
    GNNService,
)


# Fixtures
@pytest.fixture
def sample_triples():
    """Sample knowledge graph triples"""
    return [
        Triple('Python', 'is_a', 'ProgrammingLanguage'),
        Triple('Python', 'used_for', 'DataScience'),
        Triple('Python', 'created_by', 'GuidoVanRossum'),
        Triple('Java', 'is_a', 'ProgrammingLanguage'),
        Triple('Java', 'used_for', 'Enterprise'),
        Triple('DataScience', 'requires', 'Statistics'),
    ]


@pytest.fixture
def simple_graph():
    """Simple graph structure"""
    edges = [
        ('A', 'B'),
        ('B', 'C'),
        ('A', 'C'),
    ]
    
    features = {
        'A': np.random.randn(128).astype(np.float32),
        'B': np.random.randn(128).astype(np.float32),
        'C': np.random.randn(128).astype(np.float32),
    }
    
    return GraphStructure(
        edges=edges,
        node_features=features,
        num_nodes=3,
        num_edges=3
    )


# Node Embedder Tests
class TestNodeEmbedder:
    """Test node embedding training"""
    
    def test_transe_initialization(self):
        """Test TransE embedder initialization"""
        embedder = NodeEmbedder(method=EmbeddingMethod.TRANSE)
        assert embedder.method == EmbeddingMethod.TRANSE
        assert embedder.algorithm is None  # Not trained yet
    
    def test_train_transe(self, sample_triples):
        """Test TransE training"""
        embedder = NodeEmbedder(method=EmbeddingMethod.TRANSE)
        
        config = EmbeddingConfig(
            embedding_dim=64,
            num_epochs=10,
            batch_size=4
        )
        
        results = embedder.train(sample_triples, config)
        
        assert 'final_loss' in results
        assert 'num_entities' in results
        assert results['num_entities'] >= 6  # At least 6 unique entities
        assert embedder.algorithm.is_trained
    
    def test_train_distmult(self, sample_triples):
        """Test DistMult training"""
        embedder = NodeEmbedder(method=EmbeddingMethod.DISTMULT)
        
        config = EmbeddingConfig(embedding_dim=32, num_epochs=5)
        results = embedder.train(sample_triples, config)
        
        assert results['embedding_dim'] == 32
        assert embedder.algorithm is not None
    
    def test_train_complex(self, sample_triples):
        """Test ComplEx training"""
        embedder = NodeEmbedder(method=EmbeddingMethod.COMPLEX)
        
        config = EmbeddingConfig(embedding_dim=64, num_epochs=10)
        results = embedder.train(sample_triples, config)
        
        assert embedder.algorithm.is_trained
        assert results['final_loss'] >= 0
    
    def test_get_embedding(self, sample_triples):
        """Test retrieving embeddings"""
        embedder = NodeEmbedder(method=EmbeddingMethod.TRANSE)
        
        config = EmbeddingConfig(embedding_dim=64, num_epochs=5)
        embedder.train(sample_triples, config)
        
        python_emb = embedder.get_embedding('Python')
        
        assert python_emb is not None
        assert python_emb.shape == (64,)
    
    def test_find_similar_entities(self, sample_triples):
        """Test similarity search"""
        embedder = NodeEmbedder(method=EmbeddingMethod.COMPLEX)
        
        config = EmbeddingConfig(embedding_dim=64, num_epochs=10)
        embedder.train(sample_triples, config)
        
        similar = embedder.find_similar_entities('Python', top_k=3)
        
        assert len(similar) <= 3
        assert all(isinstance(s, tuple) for s in similar)
        assert all(len(s) == 2 for s in similar)  # (entity, score)


# Graph Convolution Tests
class TestGraphConvolution:
    """Test graph convolution layers"""
    
    def test_gcn_forward(self, simple_graph):
        """Test GCN forward pass"""
        gcn = GraphConvolution(
            convolution_type=ConvolutionType.GCN,
            layer_dims=[128, 64, 32]
        )
        
        output = gcn.forward(simple_graph, simple_graph.node_features)
        
        assert len(output) == 3  # Same number of nodes
        assert all(emb.shape == (32,) for emb in output.values())  # Output dim
    
    def test_gat_forward(self, simple_graph):
        """Test GAT forward pass"""
        gat = GraphConvolution(
            convolution_type=ConvolutionType.GAT,
            layer_dims=[128, 64]
        )
        
        output = gat.forward(simple_graph, simple_graph.node_features)
        
        assert len(output) == 3
        # GAT concatenates 4 heads of dim 16, so output is 64
        assert all(emb.shape[0] > 0 for emb in output.values())
    
    def test_graph_structure_neighbors(self, simple_graph):
        """Test graph structure neighbor lookup"""
        neighbors_a = simple_graph.get_neighbors('A')
        
        assert 'B' in neighbors_a
        assert 'C' in neighbors_a
    
    def test_graph_structure_degree(self, simple_graph):
        """Test degree computation"""
        degree_a = simple_graph.get_degree('A')
        degree_b = simple_graph.get_degree('B')
        
        assert degree_a >= 2  # A connects to B and C
        assert degree_b >= 2  # B connects from A and to C


# Link Predictor Tests
class TestLinkPredictor:
    """Test link prediction"""
    
    @pytest.fixture
    def trained_predictor(self, sample_triples):
        """Create trained link predictor"""
        embedder = NodeEmbedder(method=EmbeddingMethod.COMPLEX)
        
        config = EmbeddingConfig(embedding_dim=64, num_epochs=20)
        embedder.train(sample_triples, config)
        
        predictor = LinkPredictor(scoring_function=ScoringFunction.COMPLEX)
        predictor.set_embeddings(
            embedder.algorithm.entity_embeddings,
            embedder.algorithm.relation_embeddings
        )
        predictor.add_known_triples([
            (t.head, t.relation, t.tail) for t in sample_triples
        ])
        
        return predictor
    
    def test_predict_tail(self, trained_predictor):
        """Test tail prediction"""
        predictions = trained_predictor.predict_tail(
            'Python', 'is_a', top_k=5, filter_known=False
        )
        
        assert len(predictions) > 0
        assert all(hasattr(p, 'tail') for p in predictions)
        assert all(hasattr(p, 'score') for p in predictions)
        assert all(hasattr(p, 'rank') for p in predictions)
        
        # Predictions should be sorted by score
        if len(predictions) > 1:
            assert predictions[0].score >= predictions[1].score
    
    def test_predict_head(self, trained_predictor):
        """Test head prediction"""
        predictions = trained_predictor.predict_head(
            'is_a', 'ProgrammingLanguage', top_k=5
        )
        
        assert len(predictions) > 0
    
    def test_predict_relation(self, trained_predictor):
        """Test relation prediction"""
        relations = trained_predictor.predict_relation(
            'Python', 'DataScience', top_k=3
        )
        
        assert len(relations) > 0
        assert all(isinstance(r, tuple) for r in relations)
        assert all(len(r) == 2 for r in relations)  # (relation, score)
    
    def test_multi_hop_reasoning(self, trained_predictor):
        """Test multi-hop reasoning"""
        results = trained_predictor.multi_hop_reasoning(
            start_entity='Python',
            relation_path=['used_for', 'requires'],
            top_k=3
        )
        
        # Should find entities reachable via 2-hop path
        assert isinstance(results, list)
    
    def test_filter_known_triples(self, trained_predictor):
        """Test filtering of known triples"""
        predictions_filtered = trained_predictor.predict_tail(
            'Python', 'is_a', top_k=10, filter_known=True
        )
        
        predictions_unfiltered = trained_predictor.predict_tail(
            'Python', 'is_a', top_k=10, filter_known=False
        )
        
        # Filtered should not contain 'ProgrammingLanguage' (known)
        filtered_tails = [p.tail for p in predictions_filtered]
        assert 'ProgrammingLanguage' not in filtered_tails or len(predictions_filtered) >= 10


# GNN Service Tests
class TestGNNService:
    """Test GNN service integration"""
    
    @pytest.mark.asyncio
    async def test_train_embeddings(self, sample_triples):
        """Test embedding training via service"""
        service = GNNService()
        
        triples_dict = [
            {'head': t.head, 'relation': t.relation, 'tail': t.tail}
            for t in sample_triples
        ]
        
        result = await service.train_embeddings(
            model_id='test_model',
            triples=triples_dict,
            embedding_method=EmbeddingMethod.COMPLEX
        )
        
        assert 'model_id' in result
        assert 'num_entities' in result
        assert 'quality' in result
        
        # Cleanup
        await service.delete_model('test_model')
    
    @pytest.mark.asyncio
    async def test_predict_link(self, sample_triples):
        """Test link prediction via service"""
        service = GNNService()
        
        triples_dict = [
            {'head': t.head, 'relation': t.relation, 'tail': t.tail}
            for t in sample_triples
        ]
        
        await service.train_embeddings(
            model_id='link_test',
            triples=triples_dict,
            embedding_method=EmbeddingMethod.DISTMULT,
            config=EmbeddingConfig(embedding_dim=32, num_epochs=10)
        )
        
        predictions = await service.predict_link(
            model_id='link_test',
            head='Python',
            relation='used_for',
            top_k=3
        )
        
        assert len(predictions) > 0
        assert all('tail' in p for p in predictions)
        assert all('score' in p for p in predictions)
        
        # Cleanup
        await service.delete_model('link_test')
    
    @pytest.mark.asyncio
    async def test_multi_hop_reasoning(self, sample_triples):
        """Test multi-hop reasoning via service"""
        service = GNNService()
        
        triples_dict = [
            {'head': t.head, 'relation': t.relation, 'tail': t.tail}
            for t in sample_triples
        ]
        
        await service.train_embeddings(
            model_id='multihop_test',
            triples=triples_dict,
            embedding_method=EmbeddingMethod.COMPLEX,
            config=EmbeddingConfig(embedding_dim=64, num_epochs=15)
        )
        
        results = await service.multi_hop_reasoning(
            model_id='multihop_test',
            start_entity='Python',
            relation_path=['used_for', 'requires'],
            top_k=2
        )
        
        assert isinstance(results, list)
        
        # Cleanup
        await service.delete_model('multihop_test')
    
    @pytest.mark.asyncio
    async def test_model_management(self, sample_triples):
        """Test model CRUD operations"""
        service = GNNService()
        
        triples_dict = [t.__dict__ for t in sample_triples]
        
        # Create
        await service.train_embeddings(
            model_id='crud_test',
            triples=triples_dict,
            embedding_method=EmbeddingMethod.TRANSE
        )
        
        # Read
        model = await service.get_model('crud_test')
        assert model['model_id'] == 'crud_test'
        
        # List
        models = await service.list_models()
        assert len(models) >= 1
        
        # Delete
        success = await service.delete_model('crud_test')
        assert success is True
        
        # Verify deleted
        models_after = await service.list_models()
        model_ids = [m['model_id'] for m in models_after]
        assert 'crud_test' not in model_ids


# Integration Tests
class TestGNNIntegration:
    """End-to-end GNN workflow tests"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, sample_triples):
        """Test complete GNN workflow"""
        service = GNNService()
        
        # 1. Train embeddings
        triples_dict = [
            {'head': t.head, 'relation': t.relation, 'tail': t.tail}
            for t in sample_triples
        ]
        
        train_result = await service.train_embeddings(
            model_id='workflow_test',
            triples=triples_dict,
            embedding_method=Embedding Method.COMPLEX,
            config=EmbeddingConfig(embedding_dim=128, num_epochs=25)
        )
        
        assert train_result['num_entities'] >= 6
        
        # 2. Predict links
        tail_preds = await service.predict_link(
            model_id='workflow_test',
            head='Python',
            relation='used_for',
            top_k=5
        )
        
        assert len(tail_preds) > 0
        
        # 3. Find similar
        similar = await service.find_similar_entities(
            model_id='workflow_test',
            entity='Python',
            top_k=3
        )
        
        assert len(similar) > 0
        
        # 4. Get embedding
        embedding = await service.get_embedding(
            model_id='workflow_test',
            entity='Python'
        )
        
        assert embedding is not None
        assert len(embedding) == 128
        
        # Cleanup
        await service.delete_model('workflow_test')
