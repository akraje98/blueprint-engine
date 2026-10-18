from neo4j import AsyncGraphDatabase, AsyncDriver
import logging

logger = logging.getLogger("blueprint.graph_db")

class GraphDatabaseService:
    """Manages the lifecycle and connection pool for the Neo4j Graph Database."""
    
    def __init__(self):
        # We target port 7687 for Bolt connections. 
        # Using localhost because your FastAPI app runs locally on your Mac, talking to the container port.
        self.uri: str = "bolt://localhost:7687"
        self.username: str = "neo4j"
        self.password: str = "blueprintsecurepass123"
        self.driver: AsyncDriver | None = None

    async def connect(self) -> None:
        """Initializes the asynchronous Neo4j connection pool."""
        if not self.driver:
            try:
                self.driver = AsyncGraphDatabase.driver(
                    self.uri, 
                    auth=(self.username, self.password)
                )
                # Verify connection viability instantly
                await self.driver.verify_connectivity()
                logger.info("Successfully established connection pool to Neo4j Graph DB.")
                print("[Neo4j] Connected to graph engine successfully over bolt://localhost:7687")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j database: {e}")
                print(f"[Neo4j Error] Connection failed: {e}")
                raise e

    async def close(self) -> None:
        """Cleanly tears down open socket pools on application shutdown."""
        if self.driver:
            await self.driver.close()
            logger.info("Closed Neo4j Graph DB connection pool.")
            print("[Neo4j] Connection pool closed cleanly.")
            self.driver = None

    def get_driver(self) -> AsyncDriver:
        """Retrieves the active, verified driver instance."""
        if not self.driver:
            raise RuntimeError("Database driver is not initialized. Did you call connect()?")
        return self.driver

# Create a single global instance to import across your app modules
graph_db = GraphDatabaseService()
