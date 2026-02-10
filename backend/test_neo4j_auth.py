import asyncio
from neo4j import AsyncGraphDatabase

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
