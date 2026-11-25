import uuid
import logging
import numpy as np
from langchain_openai import OpenAIEmbeddings
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
            await client.ft(VectorService.INDEX_NAME).info()
            print(f"[Valkey Search] Index '{VectorService.INDEX_NAME}' is already active and verified.")
            return True
        except Exception:
            pass

        schema = [
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
        ]

        try:
            definition = IndexDefinition(
                prefix=[VectorService.PREFIX_MATCH], 
                index_type=IndexType.HASH
            )
            await client.ft(VectorService.INDEX_NAME).create_index(
                fields=schema, 
                definition=definition
            )
            print(f"🚀 [Valkey Search] Multi-modal Vector Index '{VectorService.INDEX_NAME}' created successfully!")
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"[Valkey Search] Index '{VectorService.INDEX_NAME}' verified active during execution.")
                return True
            logger.error(f"Failed to compile Valkey search index: {e}")
            print(f"❌ [Valkey Search Error] Index creation failed: {e}")
            return False

    @staticmethod
    async def store_preference(workspace_id: str, content: str, category: str = "general") -> str:
        """Generates a 1536-dim embedding and stores the preference in Valkey with a unique UUID."""
        client = vector_db.get_client()
        embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # 1. Convert text string into a 1536-float vector array
        raw_vector = await embeddings_model.aembed_query(content)
        vector_bytes = np.array(raw_vector, dtype=np.float32).tobytes()
        
        # 2. Generate unique UUID key
        pref_id = f"pref_{uuid.uuid4()}"
        redis_key = f"{VectorService.PREFIX_MATCH}{pref_id}"
        
        # 3. Save Hash map into Valkey (automatically indexed by HNSW)
        await client.hset(
            redis_key,
            mapping={
                "preference_id": pref_id,
                "workspace_id": workspace_id,
                "category": category,
                "content": content,
                "vector_embedding": vector_bytes
            }
        )
        return pref_id

vector_service = VectorService()
