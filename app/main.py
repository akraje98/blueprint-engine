from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

# Import our global data warehouse and process singletons
from app.core.graph_db import graph_db
from app.core.vector_db import vector_db
from app.core.mcp_client import mcp_client
from app.services.vector_service import vector_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---------------------------------------------------------
    # STARTUP LAYER: Runs BEFORE the server accepts user traffic
    # ---------------------------------------------------------
    print("[Startup] Triggering system cluster initializations...")
    
    try:
        # 1. Boot up the Neo4j Graph DB Bolt pool
        await graph_db.connect()
        
        # 2. Boot up the Valkey Vector DB memory sockets
        await vector_db.connect()
        await vector_service.create_vector_index(dim=1536)
        
        # 3. Spawn and bind the isolated local MCP server subprocess plug live!
        await mcp_client.connect()
        
    except Exception as e:
        print(f"[Critical Startup Error] Cluster initialization failed: {e}")
        raise e
        
    yield  # ⏸️ PAUSE: Server is online, fully integrated, and listening!

    # ---------------------------------------------------------
    # SHUTDOWN LAYER: Runs AFTER you close down the server
    # ---------------------------------------------------------
    print("[Shutdown] Severing cluster connection pools safely...")
    
    # Terminate background tasks and sever open socket tracks cleanly
    await mcp_client.close()
    await graph_db.close()
    await vector_db.close()


app = FastAPI(
    title="BluePrint Engine API",
    description="Generic production-grade Agentic API for multi-modal project tracking",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {
        "status": "online", 
        "engine": "BluePrint Core Engine",
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "engine": "BluePrint Framework Core"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
