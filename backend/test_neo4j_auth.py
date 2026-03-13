import asyncio
import os
from neo4j import AsyncGraphDatabase
import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_NEO4J_AUTH_TEST") != "1",
    reason="Manual Neo4j auth check. Set RUN_NEO4J_AUTH_TEST=1 to run.",
)


@pytest.mark.asyncio
async def test_auth():
    uri = "bolt://localhost:7687"
    passwords = ["devpassword", "neo4j", "password", "admin"]
    
    print(f"Testing Neo4j connection to {uri}...")
    
    for pwd in passwords:
        print(f"Trying user='neo4j', password='{pwd}'...", end=" ")
        try:
            driver = AsyncGraphDatabase.driver(uri, auth=("neo4j", pwd))
            await driver.verify_connectivity()
            print("✅ SUCCESS!")
            await driver.close()
            return pwd
        except Exception as e:
            print(f"❌ Failed ({e})")
            
    print("\nAll passwords failed.")
    return None

if __name__ == "__main__":
    asyncio.run(test_auth())
