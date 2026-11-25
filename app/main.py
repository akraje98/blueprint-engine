from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

# Load environment variables (such as OPENAI_API_KEY) from .env
load_dotenv()

# Import singletons and compiled LangGraph workflow
from app.core.graph_db import graph_db
from app.core.vector_db import vector_db
from app.core.mcp_client import mcp_client
from app.services.vector_service import vector_service
from app.agents.graph import blueprint_graph
from app.schemas.agent_state import BlueprintAgentState

# Request schema for incoming chat messages
class ChatRequest(BaseModel):
    message: str
    workspace_id: str = "default_workspace"

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Startup] Triggering system cluster initializations...")
    try:
        await graph_db.connect()
        await vector_db.connect()
        await vector_service.create_vector_index(dim=1536)
        await mcp_client.connect()
    except Exception as e:
        print(f"[Critical Startup Error] Cluster initialization failed: {e}")
        raise e
        
    yield

    print("[Shutdown] Severing cluster connection pools safely...")
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

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Triggers the LangGraph stateful multi-agent workflow."""
    try:
        # 1. Initialize the shared state notebook with the user's message
        initial_state : BlueprintAgentState = {
            "messages": [{"role": "user", "content": request.message}],
            "current_intent": "UNKNOWN",
            "workspace_id": request.workspace_id,
            "extracted_entities": [],
            "extracted_events": [],
            "extracted_preferences": [],
            "audit_report": {}
        }
        
        # 2. Run the compiled LangGraph assembly line
        final_state = await blueprint_graph.ainvoke(initial_state)
        
        # 3. Return the structured results from the state notebook
        return {
            "status": "success",
            "intent": final_state.get("current_intent"),
            "extracted_events": final_state.get("extracted_events"),
            "extracted_preferences": final_state.get("extracted_preferences"),
            "audit_report": final_state.get("audit_report")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
