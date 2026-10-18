import redis.asyncio as aioredis
import logging

logger = logging.getLogger("blueprint.vector_db")

class VectorDatabaseService:
    """Manages the lifecycle and connection pool for the Valkey Semantic Vector DB."""
    
    def __init__(self):
        # We target port 6380 (the custom port mapping we set in docker-compose)
        # to avoid colliding with your other local practice container on 6379!
        self.host: str = "localhost"
        self.port: int = 6380
        self.client: aioredis.Redis | None = None

    async def connect(self) -> None:
        """Initializes the asynchronous Valkey connection pool."""
        if not self.client:
            try:
                # Initialize an async connection pool targeting our custom port 6380
                self.client = aioredis.Redis(
                    host=self.host, 
                    port=self.port, 
                    decode_responses=True # Automatically converts raw bytes to Python strings
                )
                # Verify container responsiveness by issuing a quick ping command
                await self.client.ping()
                logger.info("Successfully established connection pool to Valkey Vector DB.")
                print("[Valkey] Connected to semantic vector engine successfully over port 6380")
            except Exception as e:
                logger.error(f"Failed to connect to Valkey database: {e}")
                print(f"[Valkey Error] Connection failed: {e}")
                raise e

    async def close(self) -> None:
        """Cleanly closes the connection pool on application shutdown."""
        if self.client:
            await self.client.close()
            logger.info("Closed Valkey Vector DB connection pool.")
            print("[Valkey] Connection pool closed cleanly.")
            self.client = None

    def get_client(self) -> aioredis.Redis:
        """Retrieves the active, verified Valkey client instance."""
        if not self.client:
            raise RuntimeError("Valkey client is not initialized. Did you call connect()?")
        return self.client

# Create a single global instance using the Singleton Pattern to share across modules
vector_db = VectorDatabaseService()
