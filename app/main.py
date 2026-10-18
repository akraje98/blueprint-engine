from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

# Import the global graph database service instance we built in Task 2.1
from app.core.graph_db import graph_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---------------------------------------------------------
    # STARTUP LAYER: Runs BEFORE the server accepts user traffic
    # ---------------------------------------------------------
    print("[Startup] Triggering database client initializations...")
    
    try:
        # Fire up the Neo4j Bolt connection pool and verify connectivity live!
        await graph_db.connect()
    except Exception as e:
        print(f"[Critical Startup Error] Could not connect to Neo4j: {e}")
        # Crashing the startup sequence safely prevents running a broken server
        raise e
        
    yield  # ⏸️ PAUSE: Server is now open and listening for API requests!

    # ---------------------------------------------------------
    # SHUTDOWN LAYER: Runs AFTER you close down the server
    # ---------------------------------------------------------
    print("[Shutdown] Closing connection pools safely...")
    # Cleanly sever open socket lines to prevent port memory leaks on your Mac
    await graph_db.close()


app = FastAPI(
    title="BluePrint Engine API",
    description="Generic production-grade Agentic API for multi-modal project tracking",
    version="1.0.0",
    lifespan=lifespan
)

# Root route to handle standard browser hits and prevent 404 errors
@app.get("/")
async def root():
    return {
        "status": "online", 
        "engine": "BluePrint Core Engine",
        "documentation": "/docs"
    }

# Explicit health check route to verify system vitals
@app.get("/health")
async def health_check():
    return {"status": "healthy", "engine": "BluePrint Framework Core"}

if __name__ == "__main__":
    # Using 'app.main:app' to ensure proper relative module lookup from the root folder
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
