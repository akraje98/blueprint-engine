# 🗺️ BluePrint Project State Blueprint

## 🏗️ Core Stack Configurations
* **Project Name:** BluePrint (Generic Full-Stack AI Milestone & Event Tracker)
* **Backend Framework:** FastAPI (Asynchronous lifespan mode) on Port 8000 (`GET /`, `GET /health`, `POST /chat`)
* **Graph Layer:** Neo4j (image: 5.12.0-community) on Bolt Port 7687 (UI Port 7474)
* **Vector/Cache Layer:** Valkey Bundle on Port 6380 (UI Admin Tool on Port 8080) with `blueprint_preferences_idx` HNSW index
* **MCP Server Integration:** Standalone modern v2 process (`mcp_server/server.py`) communicating over stdio channels, watching `~/blueprint_ingest`
* **Agentic Layer:** LangGraph & LangChain Core (`app/agents/`) with OpenAI `gpt-4o` & `text-embedding-3-small` (loaded via `.env`)
* **IDE:** Cursor (Configured with `pyrightconfig.json` and `__init__.py` package markers)

## 🌿 Git State
* **Current Working Branch:** `main` (Merged through Phase 4 Core Agentic Backend)

## 🏁 Completed Milestones
* **Phase 1 (Complete):** Root layout, `.venv`, `.gitignore` (protecting `.env` and Neo4j logs), and FastAPI `lifespan` shell.
* **Phase 2 (Complete):** Dual-Storage Hybrid RAG Engine.
  * `app/core/graph_db.py` & `vector_db.py`: Async connection pools with clean shutdown teardowns.
  * `app/services/graph_service.py`: Parameterized Cypher CRUD wrappers, JSON dictionary flattening, and workspace-scoped `check_time_conflict` queries.
  * `app/services/vector_service.py`: Automated HNSW vector index setup and `store_preference` (1536-dim embeddings with `uuid4()` keys).
* **Phase 3 (Complete):** Local Ingestion Gateway (`mcp_server/server.py` & `app/core/mcp_client.py`) using `MCPServer` v2 and `StdioServerParameters` for sandboxed file discovery.
* **Phase 4 (Core Complete & Verified):**
  * `app/schemas/agent_state.py`: Created `BlueprintAgentState` TypedDict shared state schema.
  * `app/agents/nodes.py`: Built `parsing_router_node` (with dynamic date injection), `conflict_auditor_node` (Neo4j clash detection), and `persistence_node` (multi-tenant `uuid4()` writes to Neo4j and Valkey).
  * `app/agents/graph.py`: Compiled LangGraph state machine with conditional `route_after_audit` branching.
  * `app/main.py`: Exposed `POST /chat` endpoint and verified live event creation, vector indexing, and conflict blocking in Swagger UI.

## 🎯 Next Immediate Step
* **Phase 4 Enhancement / Phase 5 Frontend:** Either wire MCP local file reading (`~/blueprint_ingest`) + Valkey preference retrieval directly into the chat agent loop, or start building the **React 3-Panel Dashboard UI** to visualize the chat, timeline, and databases.
