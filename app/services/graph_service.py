import json
from typing import Dict, Any, Optional
from app.core.graph_db import graph_db
from neo4j import Query
from typing import Dict, Any, Optional, LiteralString, cast


class GraphService:
    """Handles abstract CRUD operations and parameterized Cypher queries for BluePrint."""

    @staticmethod
    def _serialize_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures nested dictionaries are flattened into JSON strings for Neo4j primitives compatibility."""
        processed = {}
        for key, value in properties.items():
            if isinstance(value, dict):
                # Convert the nested map into a safe flat string primitive
                processed[key] = json.dumps(value)
            else:
                processed[key] = value
        return processed

    @staticmethod
    def _deserialize_properties(node_properties: Dict[str, Any]) -> Dict[str, Any]:
        """Converts serialized JSON string properties back into clean Python dictionaries on retrieval."""
        processed = {}
        for key, value in node_properties.items():
            if isinstance(value, str):
                try:
                    # Attempt to parse back into a live python dictionary
                    processed[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    processed[key] = value
            else:
                processed[key] = value
        return processed

    @staticmethod
    async def create_node(label: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a generic node in the graph with strict parameterization and serialization handling."""
        driver = graph_db.get_driver()
        safe_label = "".join([c for c in label if c.isalnum()])
        
        # Serialize nested map structures before sending to the engine
        safe_props = GraphService._serialize_properties(properties)
        
        query = cast(LiteralString, f"""
        CREATE (n:{safe_label})
        SET n = $props, n.created_at = timestamp()
        RETURN n {{.*}} as node
        """)
        
        async with driver.session() as session:
            result = await session.run(Query(query), props=safe_props)
            record = await result.single()
            if record:
                return GraphService._deserialize_properties(record["node"])
            return {}

    @staticmethod
    async def read_node(label: str, key_field: str, key_value: Any) -> Optional[Dict[str, Any]]:
        """Reads a specific node and deserializes nested property fields cleanly."""
        driver = graph_db.get_driver()
        safe_label = "".join([c for c in label if c.isalnum()])
        safe_key = "".join([c for c in key_field if c.isalnum() or c == '_'])

        query = cast(LiteralString, f"""
        MATCH (n:{safe_label} {{{safe_key}: $value}})
        RETURN n {{.*}} as node
        """)
        
        async with driver.session() as session:
            result = await session.run(Query(query), value=key_value)
            record = await result.single()
            if record:
                return GraphService._deserialize_properties(record["node"])
            return None

    @staticmethod
    async def create_relationship(
        from_label: str, from_key: str, from_val: Any,
        to_label: str, to_key: str, to_val: Any,
        rel_type: str, rel_properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Creates a directional relationship path arrow between two matching nodes."""
        driver = graph_db.get_driver()
        
        s_from_lbl = "".join([c for c in from_label if c.isalnum()])
        s_from_key = "".join([c for c in from_key if c.isalnum() or c == '_'])
        s_to_lbl = "".join([c for c in to_label if c.isalnum()])
        s_to_key = "".join([c for c in to_key if c.isalnum() or c == '_'])
        s_rel_type = "".join([c for c in rel_type if c.isalnum() or c == '_']).upper()

        raw_props = rel_properties or {}
        safe_props = GraphService._serialize_properties(raw_props)

        query = cast(LiteralString, f"""
        MATCH (a:{s_from_lbl} {{{s_from_key}: $from_val}})
        MATCH (b:{s_to_lbl} {{{s_to_key}: $to_val}})
        CREATE (a)-[r:{s_rel_type}]->(b)
        SET r = $props
        RETURN count(r) as rel_count
        """)

        async with driver.session() as session:
            result = await session.run(Query(query), from_val=from_val, to_val=to_val, props=safe_props)
            record = await result.single()
            return record["rel_count"] > 0 if record else False

    @staticmethod
    async def check_time_conflict(
        workspace_id: str, 
        buffer_start_time: str, 
        end_time: str
    ) -> Optional[Dict[str, Any]]:
        """Checks if any existing event window overlaps with [buffer_start_time, end_time] in the same workspace."""
        if not buffer_start_time or not end_time:
            return None
            
        driver = graph_db.get_driver()
        query = cast(LiteralString, """
        MATCH (n:TimelineEvent {workspace_id: $workspace_id})
        WHERE n.buffer_start_time IS NOT NULL 
          AND n.end_time IS NOT NULL
          AND n.buffer_start_time < $end_time 
          AND n.end_time > $buffer_start_time
        RETURN n {.*} as conflict_node
        LIMIT 1
        """)
        async with driver.session() as session:
            result = await session.run(
                query, 
                workspace_id=workspace_id, 
                buffer_start_time=buffer_start_time, 
                end_time=end_time
            )
            record = await result.single()
            if record:
                return GraphService._deserialize_properties(record["conflict_node"])
            return None

    @staticmethod
    async def get_workspace_events(workspace_id: str) -> list[Dict[str, Any]]:
        """Retrieves all TimelineEvent / checklist nodes for a workspace ordered by start_time."""
        driver = graph_db.get_driver()
        query = cast(LiteralString, """
        MATCH (n:TimelineEvent {workspace_id: $workspace_id})
        RETURN n {.*} as event_node
        ORDER BY n.start_time ASC
        """)
        async with driver.session() as session:
            result = await session.run(query, workspace_id=workspace_id)
            records = await result.data()
            return [GraphService._deserialize_properties(r["event_node"]) for r in records]

    @staticmethod
    async def update_checklist_item(event_id: str, status: str, actual_cost: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Updates a checklist item's completion status and actual expenditure in Neo4j."""
        driver = graph_db.get_driver()
        query = cast(LiteralString, """
        MATCH (n:TimelineEvent {event_id: $event_id})
        SET n.status = $status,
            n.actual_cost = COALESCE($actual_cost, n.actual_cost)
        RETURN n {.*} as updated_node
        """)
        async with driver.session() as session:
            result = await session.run(query, event_id=event_id, status=status, actual_cost=actual_cost)
            record = await result.single()
            if record:
                return GraphService._deserialize_properties(record["updated_node"])
            return None



