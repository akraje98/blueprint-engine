import asyncio
from app.core.vector_db import vector_db

async def run_test():
    print("🚀 Kicking off BluePrint Live Valkey Validation...")
    
    # 1. Connect to the Valkey container pool on port 6380
    await vector_db.connect()
    client = vector_db.get_client()
    
    try:
        # ---- TEST 1: Dynamic Key-Value String Storage ----
        print("\n[Test 1] Storing a dynamic string key...")
        user_key = "user:session:active_workspace"
        workspace_id = "ws_wedding_2027"
        
        # Write to Valkey
        await client.set(user_key, workspace_id, ex=300) # ex=300 means expires in 5 minutes!
        print(f"✅ String Key Saved!")
        
        # Read from Valkey
        fetched_val = await client.get(user_key)
        print(f"📡 Retrieved from Valkey: {user_key} -> '{fetched_val}'")

        # ---- TEST 2: Dynamic Hash Map Storage (For Structured Metadata) ----
        print("\n[Test 2] Storing a dynamic Hash Map (Metadata fields)...")
        pref_key = "preference:id:pref_099"
        preference_payload = {
            "preference_id": "pref_099",
            "category": "dietary",
            "content": "Must find catering with vegetarian or gluten-free options",
            "importance": "high"
        }
        
        # Write the whole dictionary as a Valkey Hash map (HSET)
        await client.hset(pref_key, mapping=preference_payload)
        print("✅ Hash Map Fields Saved!")
        
        # Read specific fields back dynamically
        category = await client.hget(pref_key, "category")
        content = await client.hget(pref_key, "content")
        print(f"📡 Retrieved fields: Category='{category}', Content='{content}'")
        
        # Read the full dictionary back dynamically
        full_hash = await client.hgetall(pref_key)
        print(f"📋 Full metadata hash map: {full_hash}")

    except Exception as error:
        print(f"💥 Valkey test crashed with error: {error}")
        
    finally:
        # 3. Disconnect cleanly
        print("\nTearing down Valkey connection pools safely...")
        await vector_db.close()

if __name__ == "__main__":
    asyncio.run(run_test())
