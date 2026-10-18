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
* **Phase 2 - Task 2.1 (Complete):** 
  * `app/core/graph_db.py`: Async Singleton Neo4j connection pool driver wired.
  * `app/services/graph_service.py`: Automated abstract CRUD wrapper utilities completed with dynamic label sanitization and dictionary map serialization.
* **Phase 2 - Task 2.2 (In Progress - Connection Stable):**
  * `app/core/vector_db.py`: Async Singleton Valkey connection pool driver wired completely on custom port 6380 and verified via internal ping lifecycles.

## 🎯 Next Immediate Step
* **Phase 2 - Task 2.2 (Vector Layer Engine):** Build the abstract indexing utility wrappers to create the RediSearch-compatible vector metadata indexes so our future AI can run semantic text searches on user notes.
