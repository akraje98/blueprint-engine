import json
from typing import Dict, Any, Optional
from app.core.graph_db import graph_db

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
        
        query = f"""
        CREATE (n:{safe_label})
        SET n = $props, n.created_at = timestamp()
        RETURN n {{.*}} as node
        """
        
        async with driver.session() as session:
            result = await session.run(query, props=safe_props)
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

        query = f"""
        MATCH (n:{safe_label} {{{safe_key}: $value}})
        RETURN n {{.*}} as node
        """
        
        async with driver.session() as session:
            result = await session.run(query, value=key_value)
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

        query = f"""
        MATCH (a:{s_from_lbl} {{{s_from_key}: $from_val}})
        MATCH (b:{s_to_lbl} {{{s_to_key}: $to_val}})
        CREATE (a)-[r:{s_rel_type}]->(b)
        SET r = $props
        RETURN count(r) as rel_count
        """

        async with driver.session() as session:
            result = await session.run(query, from_val=from_val, to_val=to_val, props=safe_props)
            record = await result.single()
            return record["rel_count"] > 0 if record else False
