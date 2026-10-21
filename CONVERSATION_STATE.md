# 🗺️ BluePrint Project State Blueprint

## 🏗️ Core Stack Configurations
* **Project Name:** BluePrint (Generic Full-Stack AI Milestone & Event Tracker)
* **Backend Framework:** FastAPI (Asynchronous lifespan mode) on Port 8000
* **Graph Layer:** Neo4j (image: 5.12.0-community) on Bolt Port 7687 (UI Port 7474)
* **Vector/Cache Layer:** Valkey Bundle on Port 6380 (UI Admin Tool on Port 8080)
* **MCP Server Integration:** Standalone modern v2 process communicating over stdio channels.
* **IDE:** Cursor

## 🌿 Git State
* **Current Working Branch:** `main` (Fully updated with Phase 1, 2, and 3 architectures)

## 🏁 Completed Milestones
* **Phase 1 (Complete):** Root layout setup, virtual environment layout, Cursor `.gitignore` paths established. FastAPI application shell with async `lifespan` manager complete and committed.
* **Phase 2 (Complete):** Dual-Storage Hybrid RAG Engine is fully operational.
  * `app/core/graph_db.py` & `vector_db.py`: Async connection pool clients configured and tested with zero socket resource leaks.
  * `app/services/graph_service.py`: Parameterized Cypher wrappers with alphanumeric sanitization and dictionary object flattening written and validated via `test_graph.py`.
  * `app/services/vector_service.py`: Automated HNSW index setup built to handle hybrid metadata tag filtering with error-handling logic for index recovery.
* **Phase 3 (Complete):** Local Ingestion Gateway fully integrated.
  * `mcp_server/server.py`: Coded using the modern v2 `MCPServer` standard, exposing path-sanitized sandboxed tools (`list_ingest_files`, `read_ingest_file`) watching `~/blueprint_ingest`.
  * `app/core/mcp_client.py`: Async subprocess lifecycle client manager built using the strict `StdioServerParameters` format to bind stdio streams cleanly.
  * `app/main.py`: Fully wired to orchestrate automatic pool execution and hot runtime discovery of filesystem tools on backend boot.

## 🎯 Next Immediate Step
* **Phase 4 (LangGraph Stateful Multi-Agent Brain):** Construct our centralized state schema definitions, define our multi-agent router nodes, and build out the **Conflict Auditor loop** to track logical timeline collisions!
