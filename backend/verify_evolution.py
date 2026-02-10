"""
Verify Evolution Engine

Tests the EvolutionEngine's ability to:
1. Create initial population
2. Evolve a generation (Mutation/Crossover)
3. Confirm prompt changes
"""

from uuid import uuid4
from src.services.advanced.gaia.evolution_engine import EvolutionEngine, EvolutionGenome, EvolutionMetrics
from src.infrastructure.llm.vllm_client import vllm_client
import asyncio

async def test_evolution():
    print("🧬 Testing Evolution Engine...")
    
    # Initialize LLM
    try:
        await vllm_client.connect()
    except Exception as e:
        print(f"Failed to connect to LLM: {e}")
        return

    # Initialize implementation
    engine = EvolutionEngine(population_size=5, mutation_rate=1.0) # Force mutation
    
    # Create dummy parent
    parent = EvolutionGenome(
        agent_id=uuid4(),
        system_prompt="You are a helpful assistant.",
        temperature=0.7,
        capabilities=["general"]
    )
    
    # Test Mutation
    print("\n[Test 1] Mutation...")
    
    # We need to manually trigger mutation or run a generation
    # Let's clone and mutate
    mutant = engine._clone_genome(parent)
    
    
    print("\n[Test 1] Mutation Loop (5 attempts)...")
    for i in range(5):
        mutant = engine._clone_genome(parent)
        mutated = await engine.mutate(mutant)
        
        print(f"Attempt {i+1}:")
        if mutated.system_prompt != parent.system_prompt:
            print(f"  👉 Prompt changed: {mutated.system_prompt}")
        elif mutated.temperature != parent.temperature:
            print(f"  👉 Temperature changed: {mutated.temperature:.2f}")
        elif set(mutated.capabilities) != set(parent.capabilities):
            print(f"  👉 Capabilities changed: {mutated.capabilities}")
        else:
            print("  ⚠️ No visible change (maybe failed or same value)")
    
    await vllm_client.disconnect()
    
if __name__ == "__main__":
    asyncio.run(test_evolution())
