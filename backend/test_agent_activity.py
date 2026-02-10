"""
Test Script: Simulate Agent Activity

This script simulates agent task executions to test the real metrics system.
It creates realistic agent activity and records it using the MetricsCollector.
"""

import asyncio
import random
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.services.metrics.collector import MetricsCollector
from src.services.metrics.aggregator import MetricsAggregator
from src.infrastructure.metrics.redis_repository import get_cache_repository
from src.infrastructure.metrics.postgres_repository import get_metrics_repository
from src.domain.models.metrics import DreamType


async def simulate_agent_tasks():
    """Simulate various agent tasks to populate the metrics system"""
    
    print("🚀 Initializing Metrics System...")
    
    # Initialize repositories and services
    cache = await get_cache_repository()
    repository = await get_metrics_repository()
    collector = MetricsCollector(repository, cache)
    aggregator = MetricsAggregator(repository, cache)
    
    agents = [
        ("data-analyst", "Data Analyst"),
        ("designer", "Designer"),
        ("financial", "Financial Advisor"),
        ("translator", "Translator")
    ]
    
    print("\n📊 Simulating Agent Activity:\n")
    
    # Simulate 20 tasks across all agents
    for i in range(20):
        agent_id, agent_name = random.choice(agents)
        task_id = f"task-{datetime.now().timestamp()}-{i}"
        
        # Simulate task characteristics
        task_type = random.choice(["analysis", "generation", "translation", "design"])
        success = random.random() > 0.15  # 85% success rate
        response_time = random.randint(200, 1200)  # 200-1200ms
        
        print(f"  [{i+1}/20] {agent_name} executing {task_type} task...")
        
        # Record task start
        execution = await collector.record_task_start(
            agent_id=agent_id,
            agent_name=agent_name,
            task_id=task_id,
            task_type=task_type,
            input_data={"prompt": f"Test task {i}"}
        )
        
        # Simulate processing time
        await asyncio.sleep(response_time / 1000)
        
        # Record task completion
        if success:
            await collector.record_task_completion(
                execution=execution,
                success=True,
                output_data={"result": f"Completed {task_type}"},
            )
            print(f"    ✅ Success in {response_time}ms")
        else:
            await collector.record_task_completion(
                execution=execution,
                success=False,
                error_type="processing_error",
                error_message="Simulated failure"
            )
            print(f"    ❌ Failed in {response_time}ms")
    
    print("\n🏆 Simulating Tournament Matches:\n")
    
    # Simulate 5 tournament matches
    for i in range(5):
        agent1_id, agent1_name = random.choice(agents)
        agent2_id, agent2_name = random.choice([a for a in agents if a[0] != agent1_id])
        
        print(f"  [{i+1}/5] Match: {agent1_name} vs {agent2_name}")
        
        # Start match
        match = await collector.record_match_start(
            tournament_id="test-tournament-1",
            round_number=i + 1,
            agent1_id=agent1_id,
            agent2_id=agent2_id,
            match_type="standard"
        )
        
        # Determine winner
        winner_is_agent1 = random.random() > 0.5
        winner_id = agent1_id if winner_is_agent1 else agent2_id
        loser_id = agent2_id if winner_is_agent1 else agent1_id
        
        # Simulate ELO calculation (simplified K=32 formula)
        k_factor = 32
        agent1_elo = await cache.get_elo_rating(agent1_id)
        agent2_elo = await cache.get_elo_rating(agent2_id)
        
        expected_1 = 1 / (1 + 10 ** ((agent2_elo - agent1_elo) / 400))
        expected_2 = 1 - expected_1
        
        score_1 = 1.0 if winner_is_agent1 else 0.0
        score_2 = 1.0 - score_1
        
        new_elo_1 = int(agent1_elo + k_factor * (score_1 - expected_1))
        new_elo_2 = int(agent2_elo + k_factor * (score_2 - expected_2))
        
        # Record match outcome
        await collector.record_match_outcome(
            match=match,
            winner_id=winner_id,
            loser_id=loser_id,
            score_agent1=score_1,
            score_agent2=score_2,
            agent1_elo_after=new_elo_1,
            agent2_elo_after=new_elo_2
        )
        
        winner_name = agent1_name if winner_is_agent1 else agent2_name
        elo_change = abs(new_elo_1 - agent1_elo)
        print(f"    🏅 Winner: {winner_name} (ELO ±{elo_change})")
    
    print("\n💭 Simulating Dream Cycles:\n")
    
    # Simulate 3 dream cycles
    for i in range(3):
        agent_id, agent_name = random.choice(agents)
        dream_type = random.choice(list(DreamType))
        
        print(f"  [{i+1}/3] {agent_name} entering {dream_type.value} dream...")
        
        # Start dream
        dream = await collector.record_dream_start(
            agent_id=agent_id,
            dream_type=dream_type,
            cycle_number=i + 1,
            metadata={"test": True}
        )
        
        # Simulate dream processing
        await asyncio.sleep(0.5)
        
        # Generate random quality scores
        coherence = random.uniform(0.7, 1.0)
        novelty = random.uniform(0.6, 0.95)
        utility = random.uniform(0.65, 0.9)
        insights = random.randint(2, 8)
        
        # Complete dream
        await collector.record_dream_completion(
            dream=dream,
            insights_generated=insights,
            patterns_discovered=random.randint(1, 5),
            knowledge_consolidated=True,
            coherence_score=coherence,
            novelty_score=novelty,
            utility_score=utility,
            dream_narrative="Simulated dream exploration"
        )
        
        avg_quality = (coherence + novelty + utility) / 3
        print(f"    ✨ Generated {insights} insights (quality: {avg_quality:.2f})")
    
    print("\n📈 Current Metrics Summary:\n")
    
    # Get and display current metrics
    for agent_id, agent_name in agents:
        snapshot = await aggregator.get_agent_metrics(agent_id)
        print(f"  {agent_name}:")
        print(f"    Tasks: {snapshot.total_tasks} (Success Rate: {snapshot.success_rate:.1f}%)")
        print(f"    Avg Response: {snapshot.avg_response_time_ms}ms")
        print(f"    ELO Rating: {snapshot.elo_rating}")
        print(f"    Dreams: {snapshot.dream_cycles_completed}, Insights: {snapshot.insights_generated}")
        print()
    
    print("✅ Test Complete! Check the dashboard at http://localhost:3001/dashboard?tab=analytics\n")


if __name__ == "__main__":
    asyncio.run(simulate_agent_tasks())
