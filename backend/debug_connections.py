import sys
import os
import asyncio
from typing import Dict
from pathlib import Path

# Ensure we can import from src
# Assuming this script is run from backend/ directory
sys.path.append(os.getcwd())

try:
    from src.core.lifecycle import lifecycle_manager
except ImportError:
    # Try adding parent directory if run from inside backend/
    sys.path.append(str(Path(os.getcwd()).parent))
    from src.core.lifecycle import lifecycle_manager

async def debug():
    print("🔍 Starting Dependency Debugger...")
    print(f"Working Directory: {os.getcwd()}")
    try:
        # Manually trigger startup to test connections
        await lifecycle_manager.startup()
        
        status = lifecycle_manager.get_client_status()
        print("\n📊 Connection Status Report:")
        all_good = True
        for client, state in status.items():
            icon = "✅" if state == "connected" else "❌"
            if state != "connected":
                all_good = False
            print(f"{icon} {client}: {state}")
            
        if not all_good:
            print("\n⚠️  Some dependencies are unavailable!")
            print("Check docker-compose logs or local service status.")
        else:
            print("\n✅ All systems nominal.")
            
    except Exception as e:
        print(f"\n❌ Critical Error during diagnostics: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await lifecycle_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(debug())
