import json
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from mcp.types import TextContent
import uvicorn

load_dotenv()

from app.core.graph_db import graph_db
from app.core.vector_db import vector_db
from app.core.mcp_client import mcp_client
from app.services.graph_service import GraphService
from app.services.vector_service import vector_service
from app.agents.graph import blueprint_graph
from app.schemas.agent_state import BlueprintAgentState

class ChatRequest(BaseModel):
    message: str
    workspace_id: str = "default_workspace"

class ChecklistUpdateRequest(BaseModel):
    status: str = Field(..., description="'COMPLETED' or 'PENDING'")
    actual_cost: Optional[float] = Field(None, description="Actual amount paid in INR")

class ReceiptMatch(BaseModel):
    matched_event_id: str = Field("", description="The event_id from the pending checklist that this receipt confirms, or empty if no match")
    actual_cost: float = Field(0.0, description="Exact total amount paid in INR extracted from the receipt")
    summary: str = Field("", description="Short 1-line summary of what was confirmed")

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

# Enable CORS so our upcoming React Frontend (Port 5173/3000) can talk to FastAPI cleanly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "online", "engine": "BluePrint Core Engine", "documentation": "/docs"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "engine": "BluePrint Framework Core"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Triggers the LangGraph stateful multi-agent workflow."""
    try:
        initial_state: BlueprintAgentState = {
            "messages": [{"role": "user", "content": request.message}],
            "current_intent": "UNKNOWN",
            "workspace_id": request.workspace_id,
            "assistant_reply": "",
            "discovery_questions": [],
            "extracted_entities": [],
            "extracted_events": [],
            "extracted_preferences": [],
            "audit_report": {}
        }
        
        final_state = await blueprint_graph.ainvoke(initial_state)
        
        return {
            "status": "success",
            "intent": final_state.get("current_intent"),
            "assistant_reply": final_state.get("assistant_reply"),
            "discovery_questions": final_state.get("discovery_questions"),
            "checklist_items": final_state.get("extracted_events"),
            "extracted_preferences": final_state.get("extracted_preferences"),
            "audit_report": final_state.get("audit_report")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workspace/{workspace_id}/plan")
async def get_master_plan(workspace_id: str):
    """Fetches the full master plan, checklist progress, preferences, and total INR expenditure."""
    try:
        events = await GraphService.get_workspace_events(workspace_id)
        preferences = await vector_service.get_workspace_preferences(workspace_id)
        
        total_estimated = sum(float(e.get("estimated_cost", 0.0)) for e in events)
        total_actual = sum(float(e.get("actual_cost", 0.0)) for e in events)
        completed_count = sum(1 for e in events if e.get("status") == "COMPLETED")
        
        return {
            "workspace_id": workspace_id,
            "progress": {
                "completed": completed_count,
                "total": len(events)
            },
            "expenditure_inr": {
                "estimated_total": round(total_estimated, 2),
                "actual_spent": round(total_actual, 2),
                "remaining_estimated": round(max(0.0, total_estimated - total_actual), 2)
            },
            "preferences": preferences,
            "checklist_and_timeline": events
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/checklist/{event_id}")
async def update_checklist_status(event_id: str, payload: ChecklistUpdateRequest):
    """Manually checks/unchecks a checklist item and records actual INR expenditure."""
    updated = await GraphService.update_checklist_item(
        event_id=event_id,
        status=payload.status,
        actual_cost=payload.actual_cost
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Checklist item '{event_id}' not found.")
    return {"status": "updated", "item": updated}

@app.post("/workspace/{workspace_id}/sync-files")
async def sync_local_files_via_mcp(workspace_id: str):
    """Scans ~/blueprint_ingest via MCP, matches receipts to PENDING checklist items, and auto-completes them."""
    try:
        session = mcp_client.get_session()
        
        # 1. Ask MCP Server to list local files in ~/blueprint_ingest
        list_res = await session.call_tool("list_ingest_files", {})
        files: List[str] = []
        for block in (list_res.content or []):
            if isinstance(block, TextContent) and block.text:
                if block.text.startswith("["):
                    files.extend(json.loads(block.text))
                else:
                    files.append(block.text)
        
        # Filter out any MCP error strings before processing filenames
        files = [f for f in files if not f.startswith("Error")]
        
        if not files:
            return {"status": "no_files", "message": "No files found in ~/blueprint_ingest.", "auto_completed": []}
            
        # 2. Fetch pending checklist items from Neo4j
        all_events = await GraphService.get_workspace_events(workspace_id)
        pending_items = [e for e in all_events if e.get("status") == "PENDING"]
        
        if not pending_items:
            return {"status": "up_to_date", "files_scanned": files, "auto_completed": []}
            
        # 3. Read each file via MCP and reconcile against pending items
        matcher_llm = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(ReceiptMatch)  # type: ignore[call-arg]
        auto_completed = []
        
        for filename in files:
            read_res = await session.call_tool("read_ingest_file", {"filename": filename})
            first_read_block = read_res.content[0] if read_res.content else None
            file_content = first_read_block.text if isinstance(first_read_block, TextContent) else ""

            
            prompt = (
                f"Match this downloaded receipt/note against the pending checklist items.\n"
                f"Pending Items: {json.dumps([{'event_id': p['event_id'], 'title': p['title']} for p in pending_items])}\n"
                f"File ({filename}) Content:\n{file_content}"
            )
            match = await matcher_llm.ainvoke(prompt)
            if isinstance(match, ReceiptMatch) and match.matched_event_id:
                updated_item = await GraphService.update_checklist_item(
                    event_id=match.matched_event_id,
                    status="COMPLETED",
                    actual_cost=match.actual_cost
                )
                if updated_item:
                    auto_completed.append({
                        "file": filename,
                        "summary": match.summary,
                        "item": updated_item
                    })
                    
        return {
            "status": "synced",
            "files_scanned": files,
            "auto_completed": auto_completed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
