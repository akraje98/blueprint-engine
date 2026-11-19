# 🗺️ BluePrint Project State Blueprint

## 🏗️ Core Stack Configurations
* **Project Name:** BluePrint (Generic Full-Stack AI Milestone & Event Tracker)
* **Backend Framework:** FastAPI (Asynchronous lifespan mode) on Port 8000
* **Graph Layer:** Neo4j (image: 5.12.0-community) on Bolt Port 7687 (UI Port 7474)
* **Vector/Cache Layer:** Valkey Bundle on Port 6380 (UI Admin Tool on Port 8080)
* **MCP Server Integration:** Standalone modern v2 process (`mcp_server/server.py`) communicating over stdio channels, watching `~/blueprint_ingest`.
* **Agentic Layer:** LangGraph & LangChain Core (`app/agents/`).
* **IDE:** Cursor (Configured with `pyrightconfig.json` and `__init__.py` package markers)

## 🌿 Git State
* **Current Working Branch:** `main` (Merged up through Phase 4 Task 4.2)

## 🏁 Completed Milestones
* **Phase 1 (Complete):** Root layout, virtual environment (`.venv`), Cursor `.gitignore` rules, and FastAPI `lifespan` shell.
* **Phase 2 (Complete):** Dual-Storage Hybrid RAG Engine.
  * `app/core/graph_db.py` & `vector_db.py`: Async connection pools with clean shutdown teardowns.
  * `app/services/graph_service.py`: Parameterized Cypher CRUD wrappers with alphanumeric sanitization and JSON dictionary flattening.
  * `app/services/vector_service.py`: Automated HNSW vector index (`blueprint_preferences_idx`) setup with graceful `"already exists"` recovery.
* **Phase 3 (Complete):** Local Ingestion Gateway (`mcp_server/server.py` & `app/core/mcp_client.py`) using `MCPServer` v2 and `StdioServerParameters` for sandboxed file discovery.
* **Phase 4 - Tasks 4.1 & 4.2 (Complete):**
  * `app/schemas/agent_state.py`: Created `BlueprintAgentState` TypedDict shared memory schema.
  * `app/agents/nodes.py`: Built `parsing_router_node` (structured LLM extraction via `ExtractedPayload`) and `conflict_auditor_node` (deterministic Neo4j validation).

## 🎯 Next Immediate Step
* **Phase 4 - Task 4.3:** Create `app/agents/graph.py` to compile the LangGraph state machine with conditional self-correction edges, connect real Neo4j conflict queries inside `conflict_auditor_node`, and expose a `POST /chat` endpoint in FastAPI to test the AI brain live.
