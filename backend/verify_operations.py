"""
Verify Operations Module (Executive Agent)

Tests the ExecutiveAgent's ability to:
1. Make strategic decisions (Text)
2. Route tasks to other agents (JSON - to be implemented)
"""

import asyncio
from src.domain.models import Agent, AgentType, AgentStatus
from src.services.agents.specialized_agents import ExecutiveAgent
from src.infrastructure.llm.vllm_client import vllm_client

async def test_operations():
    print("👔 Testing Executive Agent...")
    
    # Initialize LLM
    try:
        await vllm_client.connect()
    except Exception as e:
        print(f"Failed to connect to LLM: {e}")
        return
        
    # Create Agent
    agent_model = Agent(
        id="exec-1", 
        name="Executive", 
        agent_type=AgentType.EXECUTIVE, 
        status=AgentStatus.IDLE,
        capabilities=["decision_making", "strategic_planning"],
        system_prompt="You are an Executive Agent."
    )
    agent = ExecutiveAgent(agent_model)
    
    # 1. Strategic Decision
    print("\n[Test 1] Strategic Decision...")
    try:
        result = await agent.process({
            "situation": "Our server costs are increasing by 20% month-over-month. We need to cut costs without reducing performance."
        })
        print(f"✅ Decision: {result.get('response')[:100]}...")
    except Exception as e:
        print(f"❌ Decision Failed: {e}")
        
    # 2. Routing Task (Simulated)
    print("\n[Test 2] Task Routing...")
    try:
        # Test explicit routing logic
        result = await agent.process({
            "situation": "We need to fix a memory leak in the redis cache component. Assign this to the right team member.",
            "routing_request": True
        })
        print(f"✅ Routing Decision: {result}")
        
        if result.get("type") == "routing_decision":
             print(f"🎯 Target Agent: {result.get('target')}")
        else:
             print("⚠️ Routing failed to return structured data.")
    except Exception as e:
        print(f"❌ Routing Failed: {e}")
        
    await vllm_client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_operations())
