"""
Verify Analytics Module

Tests the DataAnalystAgent with a real dataset to verify:
1. Data profiling (Pandas)
2. Statistical tests (Pandas/Scipy)
3. Visualization (Mock/Pandas)
4. Analysis Summary (LLM - to be implemented)
5. SQL Generation (LLM - to be implemented)
"""

import asyncio
import pandas as pd
from src.services.agents.data_analyst_agent import create_data_analyst_agent
from src.infrastructure.llm.vllm_client import vllm_client

async def test_analytics():
    print("📊 Testing Data Analyst Agent...")
    
    # Initialize LLM
    try:
        await vllm_client.connect()
    except Exception as e:
        print(f"Failed to connect to LLM: {e}")
        return
    
    agent = create_data_analyst_agent()
    
    # 1. Create dummy dataset
    csv_data = """id,category,value,date
1,A,10.5,2023-01-01
2,B,20.1,2023-01-02
3,A,12.3,2023-01-03
4,C,15.8,2023-01-04
5,B,22.4,2023-01-05
6,A,9.8,2023-01-06
7,C,16.2,2023-01-07
8,A,100.0,2023-01-08
"""
    print(f"Dataset:\n{csv_data}")
    
    # 2. Test Analysis (Profiling + Summary)
    print("\n[Test 1] Analyzing Dataset (Profiling + Summary)...")
    try:
        result = await agent.process({
            "action": "analyze",
            "data_csv": csv_data,
            "include_visualizations": True,
            "include_statistical_tests": True
        })
        
        print("✅ Analysis Complete!")
        print(f"Summary: {result.get('summary')}")
        print(f"Insights: {len(result.get('insights', []))}")
        print(f"Recommendations: {len(result.get('recommendations', []))}")
        
    except Exception as e:
        print(f"❌ Analysis Failed: {e}")
        
    # 3. Test SQL Generation
    print("\n[Test 2] Generating SQL...")
    try:
        sql_result = await agent.process({
            "action": "sql",
            "natural_language": "Calculate the average value per category",
            "schema": {"sales": ["id", "category", "value", "date"]}
        })
        print(f"✅ SQL Generated: {sql_result.get('sql_query')}")
        
    except Exception as e:
        print(f"❌ SQL Generation Failed: {e}")
        
    await vllm_client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_analytics())
