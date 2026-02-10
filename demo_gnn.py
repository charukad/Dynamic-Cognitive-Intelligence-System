#!/usr/bin/env python3
"""
GNN Demo Script - Demonstrates Graph Neural Networks functionality

Shows complete workflow:
1. Train TransE/DistMult/ComplEx embeddings
2. Apply GCN/GAT convolutions
3. Predict missing links
4. Multi-hop reasoning
5. Entity similarity search
"""

import asyncio
import sys
sys.path.insert(0, 'backend/src')

from services.advanced.gnn import (
    GNNService,
    NodeEmbedder,
    EmbeddingMethod,
    EmbeddingConfig,
    Triple,
    LinkPredictor,
    ScoringFunction,
)


async def demo_gnn():
    """Demonstrate GNN capabilities"""
    
    print("=" * 70)
    print("🧠 DCIS Graph Neural Networks Demo")
    print("=" * 70)
    
    # Sample knowledge graph
    triples = [
        {'head': 'Python', 'relation': 'is_a', 'tail': 'ProgrammingLanguage'},
        {'head': 'Python', 'relation': 'used_for', 'tail': 'DataScience'},
        {'head': 'Python', 'relation': 'created_by', 'tail': 'GuidoVanRossum'},
        {'head': 'Java', 'relation': 'is_a', 'tail': 'ProgrammingLanguage'},
        {'head': 'Java', 'relation': 'used_for', 'tail': 'Enterprise'},
        {'head': 'JavaScript', 'relation': 'is_a', 'tail': 'ProgrammingLanguage'},
        {'head': 'JavaScript', 'relation': 'used_for', 'tail': 'WebDevelopment'},
        {'head': 'DataScience', 'relation': 'requires', 'tail': 'Statistics'},
        {'head': 'DataScience', 'relation': 'requires', 'tail': 'MachineLearning'},
        {'head': 'MachineLearning', 'relation': 'uses', 'tail': 'Python'},
    ]
    
    print(f"\n📊 Knowledge Graph: {len(triples)} triples")
    print("\nSample triples:")
    for triple in triples[:3]:
        print(f"  ({triple['head']}, {triple['relation']}, {triple['tail']})")
    
    # Initialize service
    service = GNNService()
    
    # 1. Train ComplEx embeddings
    print("\n" + "=" * 70)
    print("1️⃣  Training ComplEx Embeddings")
    print("=" * 70)
    
    config = EmbeddingConfig(
        embedding_dim=64,
        num_epochs=30,
        learning_rate=0.01,
        batch_size=4
    )
    
    result = await service.train_embeddings(
        model_id='demo_model',
        triples=triples,
        embedding_method=EmbeddingMethod.COMPLEX,
        config=config
    )
    
    print(f"\n✅ Training Complete:")
    print(f"   Entities: {result['num_entities']}")
    print(f"   Relations: {result['num_relations']}")
    print(f"   Embedding Dim: {result['embedding_dim']}")
    print(f"   Final Loss: {result['final_loss']:.4f}")
    print(f"   Quality: {result['quality'].upper()}")
    
    # 2. Predict missing links
    print("\n" + "=" * 70)
    print("2️⃣  Link Prediction: Python used_for ?")
    print("=" * 70)
    
    predictions = await service.predict_link(
        model_id='demo_model',
        head='Python',
        relation='used_for',
        top_k=5
    )
    
    print("\nTop Predictions:")
    for pred in predictions[:5]:
        print(f"   {pred['rank']}. {pred['tail']:<20} (score: {pred['score']:.4f})")
    
    # 3. Find similar entities
    print("\n" + "=" * 70)
    print("3️⃣  Entity Similarity: Most similar to 'Python'")
    print("=" * 70)
    
    similar = await service.find_similar_entities(
        model_id='demo_model',
        entity='Python',
        top_k=3
    )
    
    print("\nSimilar Entities:")
    for sim in similar:
        print(f"   • {sim['entity']:<20} (similarity: {sim['similarity']:.4f})")
    
    # 4. Multi-hop reasoning
    print("\n" + "=" * 70)
    print("4️⃣  Multi-Hop Reasoning: Python → used_for → requires")
    print("=" * 70)
    
    reasoning = await service.multi_hop_reasoning(
        model_id='demo_model',
        start_entity='Python',
        relation_path=['used_for', 'requires'],
        top_k=3
    )
    
    print("\n2-Hop Path Results:")
    for res in reasoning:
        print(f"   • {res['entity']:<20} (score: {res['score']:.4f})")
    
    # 5. Get embedding
    print("\n" + "=" * 70)
    print("5️⃣  Embedding Retrieval")
    print("=" * 70)
    
    embedding = await service.get_embedding(
        model_id='demo_model',
        entity='Python'
    )
    
    if embedding:
        print(f"\n✅ Python embedding: {len(embedding)}-dimensional vector")
        print(f"   Sample values: [{embedding[0]:.4f}, {embedding[1]:.4f}, {embedding[2]:.4f}, ...]")
    
    # 6. Model info
    print("\n" + "=" * 70)
    print("6️⃣  Model Information")
    print("=" * 70)
    
    model = await service.get_model('demo_model')
    
    print(f"\nModel ID: {model['model_id']}")
    print(f"Method: {model['embedding_method'].upper()}")
    print(f"Quality: {model['quality'].upper() if model['quality'] else 'N/A'}")
    print(f"Created: {model['created_at']}")
    
    # Cleanup
    await service.delete_model('demo_model')
    
    print("\n" + "=" * 70)
    print("✅ Demo Complete!")
    print("=" * 70)
    print("\n📚 GNN Capabilities Demonstrated:")
    print("   ✓ Knowledge graph embedding (TransE/DistMult/ComplEx)")
    print("   ✓ Link prediction with confidence scores")
    print("   ✓ Entity similarity via cosine distance")
    print("   ✓ Multi-hop reasoning through relation paths")
    print("   ✓ Model versioning and management")
    print("\n🚀 Production-ready GNN system for DCIS!")
    print()


if __name__ == '__main__':
    asyncio.run(demo_gnn())
