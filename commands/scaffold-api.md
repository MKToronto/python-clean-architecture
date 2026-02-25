---
name: scaffold-api
description: Generate a new FastAPI project with clean architecture
argument-hint: <project-name>
---

Generate a new FastAPI project named `$ARGUMENTS` with the three-layer clean architecture structure.

## Process

1. **Ask for entities** — Use AskUserQuestion: "What are the main entities for this API? (e.g., users, products, orders)" to determine what to scaffold.

2. **Create project structure** — Generate the full directory tree:

   ```
   {project_name}/
   ├── main.py                      # FastAPI app, include_router, startup
   ├── routers/
   │   ├── __init__.py
   │   └── {entity}.py              # APIRouter, endpoints, composition root
   ├── operations/
   │   ├── __init__.py
   │   ├── interface.py             # DataInterface Protocol + DataInterfaceStub
   │   └── {entity}.py              # Business logic, accepts DataInterface
   ├── db/
   │   ├── __init__.py
   │   ├── database.py              # Engine, SessionLocal, Base
   │   ├── db_interface.py          # Generic DBInterface implementing DataInterface
   │   └── models.py                # SQLAlchemy ORM models
   ├── models/
   │   ├── __init__.py
   │   └── {entity}.py              # Pydantic Create/Read models
   ├── tests/
   │   ├── __init__.py
   │   └── test_{entity}.py         # Tests using DataInterfaceStub
   ├── requirements.txt
   └── .gitignore
   ```

3. **Generate files** — For each entity, create:
   - **Pydantic models** — separate Create and Read models
   - **Operations** — business logic functions accepting `data_interface: DataInterface`
   - **Router** — CRUD endpoints acting as composition root, injecting concrete DB
   - **DB model** — SQLAlchemy ORM model
   - **Tests** — using `DataInterfaceStub` with no database dependency

4. **Wire it together** — `main.py` includes all routers and sets up the database.

Consult `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/layered-architecture.md` and `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/testable-api.md` for the full architecture patterns. Use `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/examples/fastapi-hotel-api/` as a working reference.
