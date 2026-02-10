"""
Verify Memory Module (Semantic Memory)

Tests the SemanticMemoryService's ability to:
1. Generate embeddings (using vLLMClient)
2. Store knowledge
3. Retrieve knowledge
"""

import asyncio
from src.services.memory.semantic_memory import semantic_memory_service
from src.infrastructure.llm.vllm_client import vllm_client
from src.infrastructure.database.chromadb_client import chroma_client
from src.infrastructure.repositories import memory_repository

async def test_memory():
    print("🧠 Testing Semantic Memory...")
    
    # Initialize LLM
    try:
        await vllm_client.connect()
    except Exception as e:
        print(f"Failed to connect to LLM: {e}")
        return
    
    # Initialize ChromaDB
    try:
        await chroma_client.connect()
        print("✅ ChromaDB connected")
    except Exception as e:
        print(f"⚠️ ChromaDB connection failed: {e} (continuing without vector storage)")

    # 1. Store Knowledge
    print("\n[Test 1] Storing Knowledge...")
    try:
        fact = "The DCIS architecture prioritizes modularity and agentic collaboration."
        memory = await semantic_memory_service.store_knowledge(
            content=fact,
            tags=["architecture", "principles"],
            importance_score=0.9
        )
        print(f"✅ Stored Memory ID: {memory.id}")
        if memory.embedding:
            print(f"✅ Embedding generated: {len(memory.embedding)} dim")
        else:
            print("⚠️ No embedding generated (Mock mode or failure)")
            
    except Exception as e:
        print(f"❌ Storage Failed: {e}")
        
    # 2. Retrieve Knowledge
    print("\n[Test 2] Retrieving Knowledge...")
    try:
        query = "What is the priority of DCIS architecture?"
        results = await semantic_memory_service.retrieve_knowledge(query)
        
        if results:
            print(f"✅ Retrieved {len(results)} results")
            print(f"Top Result: {results[0].content}")
        else:
            print("⚠️ No results found.")
            
    except Exception as e:
        print(f"❌ Retrieval Failed: {e}")

    await vllm_client.disconnect()
    await chroma_client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_memory())
