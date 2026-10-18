import asyncio
from app.core.graph_db import graph_db
from app.services.graph_service import GraphService

async def run_test():
    print("🚀 Kicking off BluePrint Live Graph Validation...")
    
    # 1. Manually open our warm connection pool
    await graph_db.connect()
    
    try:
        # 2. Create Node 1: A generic location entity
        print("\nCreating Node 1 (GenericEntity)...")
        node_1 = await GraphService.create_node(
            label="GenericEntity",
            properties={
                "entity_id": "loc_paris_001",
                "label": "Location",
                "name": "Eiffel Tower, Paris",
                "properties": {"country": "France", "climate": "Temperate"}
            }
        )
        print(f"✅ Success! Created Node: {node_1.get('name')} (ID: {node_1.get('entity_id')})")

        # 3. Create Node 2: A scheduled chronological timeline event
        print("\nCreating Node 2 (TimelineEvent)...")
        node_2 = await GraphService.create_node(
            label="TimelineEvent",
            properties={
                "event_id": "evt_tour_001",
                "title": "Guided Architecture Tour",
                "status": "PENDING",
                "associated_entities": ["loc_paris_001"]
            }
        )
        print(f"✅ Success! Created Event: {node_2.get('title')} (ID: {node_2.get('event_id')})")

        # 4. Create the directional relationship path arrow connecting them
        print("\nConnecting Node 2 to Node 1 via a structural relationship path...")
        path_created = await GraphService.create_relationship(
            from_label="TimelineEvent", from_key="event_id", from_val="evt_tour_001",
            to_label="GenericEntity", to_key="entity_id", to_val="loc_paris_001",
            rel_type="OCCURS_AT",
            rel_properties={"transportation": "Walking"}
        )
        
        if path_created:
            print("🔗 Success! Directional path drawn: (:TimelineEvent)-[:OCCURS_AT]->(:GenericEntity)")
        else:
            print("❌ Failed to create relationship path.")

    except Exception as error:
        print(f"💥 Test crashed with error: {error}")
        
    finally:
        # 5. Cleanly server the socket channels
        print("\nTearing down connection pools safely...")
        await graph_db.close()

if __name__ == "__main__":
    # Launch the async loop natively
    asyncio.run(run_test())
