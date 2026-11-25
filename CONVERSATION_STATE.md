# 🗺️ BluePrint Project State Blueprint

## 🏗️ Core Stack Configurations
* **Project Name:** BluePrint (Generic Full-Stack AI Milestone, Checklist & Expenditure Tracker)
* **Backend Framework:** FastAPI (Asynchronous lifespan mode + CORS enabled) on Port 8000
  * Endpoints: `GET /`, `GET /health`, `POST /chat`, `GET /workspace/{workspace_id}/plan`, `PATCH /checklist/{event_id}`, `POST /workspace/{workspace_id}/sync-files`
* **Graph Layer:** Neo4j (image: 5.12.0-community) on Bolt Port 7687 (UI Port 7474)
* **Vector/Cache Layer:** Valkey Bundle on Port 6380 (UI Admin Tool on Port 8080) with `blueprint_preferences_idx` HNSW index
* **MCP Server Integration:** Standalone modern v2 process (`mcp_server/server.py`) communicating over stdio channels, watching `~/blueprint_ingest`
* **Agentic Layer:** LangGraph & LangChain Core (`app/agents/`) with OpenAI `gpt-4o` & `text-embedding-3-small` (loaded via `.env`)
* **IDE:** Cursor (Configured with `pyrightconfig.json`, `__init__.py` package markers, and zero Basedpyright errors)

## 🌿 Git State
* **Current Working Branch:** `main` (Merged through Phase 4B Complete Consumer Backend)

## 🏁 Completed Milestones
* **Phase 1 (Complete):** Root layout, `.venv`, `.gitignore` (protecting `.env` and Neo4j logs), and FastAPI `lifespan` shell.
* **Phase 2 (Complete):** Dual-Storage Hybrid RAG Engine.
  * `app/core/graph_db.py` & `vector_db.py`: Async connection pools with clean shutdown teardowns.
  * `app/services/graph_service.py`: Parameterized Cypher CRUD wrappers, JSON dictionary flattening, interval-overlap `check_time_conflict` (`buffer_start_time < end_time AND end_time > buffer_start_time`), `get_workspace_events`, and `update_checklist_item`.
  * `app/services/vector_service.py`: Automated HNSW vector index setup, `store_preference` (1536-dim embeddings with `uuid4()` keys), and `get_workspace_preferences` RediSearch retrieval.
* **Phase 3 (Complete):** Local Ingestion Gateway (`mcp_server/server.py` & `app/core/mcp_client.py`) using `MCPServer` v2 and `StdioServerParameters` for sandboxed file discovery.
* **Phase 4A & 4B (Complete):** Full Consumer Agentic Backend.
  * `app/schemas/agent_state.py`: `BlueprintAgentState` TypedDict supporting `assistant_reply`, `discovery_questions`, buffer windows, booking links, and INR expenditure tracking.
  * `app/agents/nodes.py`: Built `parsing_router_node` (injects live date + Valkey preferences to pad leisure buffers, handles `DISCOVERY_FAQ` vs. `GENERATE_CHECKLIST`), `conflict_auditor_node` (interval-overlap check across all items), and `persistence_node` (multi-tenant `uuid4()` writes to Neo4j and Valkey).
  * `app/agents/graph.py`: Compiled LangGraph state machine with conditional `route_after_audit` branching.
  * `app/main.py`: Exposed all 4 consumer API endpoints (`POST /chat`, `GET /workspace/{workspace_id}/plan`, `PATCH /checklist/{event_id}`, `POST /workspace/{workspace_id}/sync-files`) with CORS middleware enabled.

## 🎯 Next Immediate Step
* **Phase 5 (React 3-Panel Dashboard UI):** Initialize the Vite + React + Tailwind frontend inside `frontend/`, connect it to FastAPI (Port 8000), and build the 3-panel workspace (Chat & Discovery FAQs + Live Neo4j Checklist/Timeline & INR Budget Bar + Valkey Preferences & MCP File Sync).
