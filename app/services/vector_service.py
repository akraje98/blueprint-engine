import logging
from redis.commands.search.field import TextField, TagField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from app.core.vector_db import vector_db

logger = logging.getLogger("blueprint.vector_service")

class VectorService:
    """Manages vector index initialization and semantic hybrid querying for Valkey Search."""
    
    INDEX_NAME = "blueprint_preferences_idx"
    PREFIX_MATCH = "preference:id:"

    @staticmethod
    async def create_vector_index(dim: int = 1536) -> bool:
        """Creates a high-performance HNSW Vector Search index with metadata filtering tags."""
        client = vector_db.get_client()
        
        try:
            # 1. Primary check: Query index details to verify if it's already active
            await client.ft(VectorService.INDEX_NAME).info()
            print(f"[Valkey Search] Index '{VectorService.INDEX_NAME}' is already active and verified.")
            return True
        except Exception:
            # Index info lookup failed, meaning it likely needs to be created
            pass

        # 2. Define the schema blueprint fields
        schema = (
            TagField("workspace_id"),
            TagField("category"),
            TextField("content"),
            VectorField(
                "vector_embedding",
                "HNSW",
                {
                    "TYPE": "FLOAT32",
                    "DIM": dim,
                    "DISTANCE_METRIC": "COSINE"
                }
            )
        )

        try:
            definition = IndexDefinition(
                prefix=[VectorService.PREFIX_MATCH], 
                index_type=IndexType.HASH
            )
            
            # 3. Compile the index inside Valkey Search
            await client.ft(VectorService.INDEX_NAME).create_index(
                fields=schema, 
                definition=definition
            )
            print(f"🚀 [Valkey Search] Multi-modal Vector Index '{VectorService.INDEX_NAME}' created successfully!")
            return True
        except Exception as e:
            error_msg = str(e)
            # Safe boundary check: If it already exists, treat it as an immediate success!
            if "already exists" in error_msg.lower():
                print(f"[Valkey Search] Index '{VectorService.INDEX_NAME}' verified active during execution.")
                return True
                
            logger.error(f"Failed to compile Valkey search index: {e}")
            print(f"❌ [Valkey Search Error] Index creation failed: {e}")
            return False

vector_service = VectorService()
