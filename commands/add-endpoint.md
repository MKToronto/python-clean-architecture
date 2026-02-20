---
name: add-endpoint
description: Scaffold a new endpoint across all three architecture layers
argument-hint: <entity-name>
---

Scaffold a new endpoint for `$ARGUMENTS` across all three layers of the clean architecture.

## Process

1. **Understand the project** — Read the existing project structure to understand naming conventions, existing patterns, and where files live. Identify the routers/, operations/, db/, and models/ directories.

2. **Ask for details** — Use AskUserQuestion to clarify:
   - "What operations does this endpoint need?" with options: CRUD (all), Read-only, Custom (describe)

3. **Generate across all layers** — Create or update files in each layer:

   **Models layer** (`models/{entity}.py`):
   - `{Entity}Create` — Pydantic model for creation input
   - `{Entity}` — Pydantic model for read output (includes id)
   - `{Entity}Update` — Pydantic model for partial updates (all fields optional)
   - `DataInterface` Protocol if not already defined, or extend existing one

   **Operations layer** (`operations/{entity}.py`):
   - Business logic functions that accept `data_interface: DataInterface`
   - `create_{entity}()`, `get_{entity}()`, `list_{entities}()`, `update_{entity}()`, `delete_{entity}()`
   - No database imports — only depends on the Protocol

   **Database layer** (`db/models.py`):
   - SQLAlchemy ORM model for the entity
   - Extend `DBInterface` if using generic implementation, or add methods to existing DB class

   **Router layer** (`routers/{entity}.py`):
   - `APIRouter` with CRUD endpoints
   - Acts as composition root — instantiates/injects concrete DB into operations
   - Proper HTTP methods and status codes (201 for create, 204 for delete)

   **Tests** (`tests/test_{entity}.py`):
   - Tests using `DataInterfaceStub` — no database needed
   - Cover create, read, update, delete, and not-found cases

4. **Update main.py** — Add `include_router()` for the new router.

Follow existing project conventions for naming, imports, and style. Consult `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/layered-architecture.md` for the layer patterns.
