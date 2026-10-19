# 🗺️ BluePrint Project State Blueprint

## 🏗️ Core Stack Configurations
* **Project Name:** BluePrint (Generic Full-Stack AI Milestone & Event Tracker)
* **Backend Framework:** FastAPI (Asynchronous lifespan mode) on Port 8000
* **Graph Layer:** Neo4j (image: 5.12.0-community) on Bolt Port 7687 (UI Port 7474)
* **Vector/Cache Layer:** Valkey Bundle on Port 6380 (UI Admin Tool on Port 8080)
* **IDE:** Cursor

## 🌿 Git State
* **Current Working Branch:** `feature/phase1`

## 🏁 Completed Milestones
* **Phase 1 (Complete):** Root layout, directory tree, Cursor `.gitignore` established. FastAPI application shell with async `lifespan` manager complete and committed.
* **Phase 2 (Complete):** Dual-Storage Hybrid RAG Engine is fully operational.
  * `app/core/graph_db.py` & `vector_db.py`: Async connection clients configured and tested.
  * `app/services/graph_service.py`: Parameterized Cypher wrappers with alphanumeric sanitization and dictionary object serialization written and validated.
  * `app/services/vector_service.py`: Automated HNSW approximate nearest neighbor index setup built to handle hybrid metadata tag filtering.
  * `app/main.py`: Fully updated to automatically initialize connection pools and build vector structures cleanly on application boot.

## 🎯 Next Immediate Step
* **Phase 3 (The Local Ingestion Gateway):** Construct a standalone, secure Model Context Protocol (MCP) server running via standard input/output (stdio) channels so our forthcoming AI agents can safely inspect files and extract raw text contexts directly from local MacBook desktop folders.
