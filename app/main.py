from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

# Import the global database service singletons we built
from app.core.graph_db import graph_db
from app.core.vector_db import vector_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---------------------------------------------------------
    # STARTUP LAYER: Runs BEFORE the server accepts user traffic
    # ---------------------------------------------------------
    print("[Startup] Triggering database client initializations...")
    
    try:
        # 1. Spin up the Neo4j Bolt connection pool
        await graph_db.connect()
        
        # 2. Spin up the Valkey connection pool over port 6380
        await vector_db.connect()
        
    except Exception as e:
        print(f"[Critical Startup Error] Could not connect to database cluster: {e}")
        # Crash the server safely to prevent execution with an uninitialized state
        raise e
        
    yield  # ⏸️ PAUSE: Server is now open and actively listening for API requests!

    # ---------------------------------------------------------
    # SHUTDOWN LAYER: Runs AFTER you close down the server
    # ---------------------------------------------------------
    print("[Shutdown] Closing connection pools safely...")
    
    # Cleanly sever open socket lines for both systems to avoid port lock memory leaks
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
