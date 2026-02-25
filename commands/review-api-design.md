---
name: review-api-design
description: Review REST API endpoints for HTTP conventions and design best practices
argument-hint: [path]
---

Review the REST API design at `$ARGUMENTS` (or the current working directory if no path given) for HTTP conventions and best practices.

## Process

1. **Read the code** — Find and read ALL Python files in the target path recursively. Focus on router/endpoint files, Pydantic models, and main.py.

2. **Check HTTP method semantics** — Verify each endpoint uses the correct method:
   - `GET` — Read-only, no side effects, cacheable
   - `POST` — Create new resource, returns 201 + Location header
   - `PUT` — Full replacement of resource, idempotent
   - `PATCH` — Partial update, uses optional fields
   - `DELETE` — Remove resource, returns 204 (no content)

3. **Check resource naming** — Verify URL conventions:
   - Plural nouns for collections (`/users`, not `/user` or `/getUsers`)
   - Nested resources for relationships (`/users/{id}/orders`)
   - No verbs in URLs (use HTTP methods instead)
   - Consistent kebab-case or snake_case (not mixed)
   - IDs in path for single resources (`/users/{user_id}`)

4. **Check status codes** — Verify appropriate codes:
   - `200` — Successful read/update
   - `201` — Resource created
   - `204` — Successful delete (no body)
   - `400` — Validation error (malformed input)
   - `404` — Resource not found
   - `422` — Unprocessable entity (FastAPI default for validation)
   - `409` — Conflict (duplicate creation)
   - `500` — Never intentionally returned

5. **Check request/response design** — Verify:
   - Separate Create and Read models (don't expose internal fields on input)
   - Update models use optional fields for partial updates
   - No sensitive data in responses (passwords, tokens, internal IDs)
   - Consistent response envelope (or lack thereof)
   - List endpoints support pagination (`skip`/`limit` or `page`/`size`)
   - Error responses have consistent format (`{"detail": "..."}`)

6. **Check API structure** — Verify:
   - Router prefix matches resource name (`/api/v1/users`)
   - Tags for OpenAPI grouping
   - Response model declarations on endpoints
   - Dependency injection for common concerns (auth, DB sessions)

7. **Report findings** — Structure output as:

   ### API Endpoint Inventory
   List all endpoints with method, path, status codes, and request/response models.

   ### What Works Well
   Specific things the API design does right.

   ### Findings by Severity
   - **Critical** — Wrong HTTP methods, missing status codes, security issues
   - **Important** — Missing pagination, inconsistent naming, no response models
   - **Suggestions** — OpenAPI tags, versioning, error format consistency

   For each finding, include file/line, the convention violated, and a fix snippet.

For detailed REST API conventions, consult:
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/rest-api-design.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/pydantic-validation.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/layered-architecture.md`
