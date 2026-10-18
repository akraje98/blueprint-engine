# 🗺️ BluePrint Project State Blueprint

## 🏗️ Core Stack Configurations
* **Project Name:** BluePrint (Generic Full-Stack AI Milestone & Event Tracker)
* **Backend Framework:** FastAPI (Asynchronous lifespan mode) on Port 8000
* **Graph Layer:** Neo4j (image: 5.12.0-community) on Bolt Port 7687 (UI Port 7474)
* **Vector/Cache Layer:** Valkey Bundle on Port 6380 (UI Admin Tool on Port 8080)
* **IDE:** Cursor

## 🌿 Git State
* **Current Working Branch:** `feature/phase1` (Main branch is pristine baseline)

## 🏁 Completed Milestones
* **Phase 1 (Complete):** Root layout, directory tree, Cursor `.gitignore` established. FastAPI application shell with async `lifespan` manager complete and committed.
* **Phase 2 - Task 2.1 (Complete):** 
  * `app/core/graph_db.py`: Async Singleton Neo4j connection pool driver wired.
  * `app/services/graph_service.py`: Automated abstract CRUD wrapper utilities completed. Features dynamic label sanitization and `json.dumps/loads` serialization to bypass Neo4j's primitive map limits.
  * `test_graph.py`: Local end-to-end verification script successfully generated nodes and paths live in Neo4j container.

## 🎯 Next Immediate Step
* **Phase 2 - Task 2.2:** Set up `app/core/vector_db.py` to initialize our asynchronous connection pool to our custom Valkey instance over port 6380.
