# REST API Design

Conventions and best practices for designing RESTful APIs with FastAPI. These guidelines complement the three-layer architecture in `layered-architecture.md` — they apply specifically to the Router layer.

---

## HTTP Method Semantics

| Method | Purpose | Idempotent | Request Body | Typical Status |
|--------|---------|------------|--------------|----------------|
| `GET` | Retrieve resource(s) | Yes | No | 200 |
| `POST` | Create a new resource | No | Yes | 201 |
| `PUT` | Replace entire resource | Yes | Yes | 200 |
| `PATCH` | Partial update | No* | Yes | 200 |
| `DELETE` | Remove a resource | Yes | No | 204 |

*PATCH is idempotent if the same partial update is applied repeatedly with the same result.

**PUT vs PATCH:** PUT replaces the entire resource (send all fields). PATCH updates only the fields included in the request body. Use `exclude_none=True` on Pydantic models for PATCH:

```python
@router.patch("/{item_id}")
async def update_item(item_id: str, data: ItemUpdate):
    return operations.update(item_id, data.model_dump(exclude_none=True), db)
```

---

## Resource Naming Conventions

- **Use plural nouns** for collections: `/customers`, `/orders`, `/rooms`
- **Use IDs for individual resources**: `/customers/{customer_id}`
- **Nest for relationships**: `/customers/{customer_id}/orders`
- **Keep nesting shallow** — max 2 levels: `/customers/{id}/orders` not `/customers/{id}/orders/{oid}/items/{iid}`
- **Use kebab-case** for multi-word resources: `/line-items`, `/booking-requests`
- **No verbs in URLs** — the HTTP method is the verb: `POST /orders` not `POST /create-order`

```python
router = APIRouter(prefix="/customers", tags=["customers"])

@router.get("/")
async def list_customers(): ...

@router.get("/{customer_id}")
async def get_customer(customer_id: str): ...

@router.post("/", status_code=201)
async def create_customer(data: CustomerCreate): ...

@router.put("/{customer_id}")
async def replace_customer(customer_id: str, data: CustomerCreate): ...

@router.patch("/{customer_id}")
async def update_customer(customer_id: str, data: CustomerUpdate): ...

@router.delete("/{customer_id}", status_code=204)
async def delete_customer(customer_id: str): ...
```

---

## Status Code Selection

### Success Codes

| Code | When | Example |
|------|------|---------|
| `200 OK` | Successful GET, PUT, PATCH | Return the resource |
| `201 Created` | Successful POST | Return the created resource |
| `204 No Content` | Successful DELETE | Return empty body |

### Client Error Codes

| Code | When | Example |
|------|------|---------|
| `400 Bad Request` | Malformed request syntax | Invalid JSON body |
| `401 Unauthorized` | Missing or invalid auth | No API key provided |
| `403 Forbidden` | Authenticated but not authorized | User can't delete others' data |
| `404 Not Found` | Resource doesn't exist | `GET /customers/nonexistent-id` |
| `409 Conflict` | State conflict | Duplicate email on registration |
| `422 Unprocessable Entity` | Validation failure | FastAPI default for Pydantic errors |

### Server Error Codes

| Code | When | Example |
|------|------|---------|
| `500 Internal Server Error` | Unhandled exception | Database connection failure |
| `503 Service Unavailable` | Temporary outage | Dependency service down |

---

## Error Response Format

Use a consistent JSON structure for all error responses:

```python
from fastapi import HTTPException

@router.get("/{customer_id}")
async def get_customer(customer_id: str):
    customer = operations.get_by_id(customer_id, db)
    if customer is None:
        raise HTTPException(
            status_code=404,
            detail={"message": f"Customer {customer_id} not found", "code": "NOT_FOUND"},
        )
    return customer
```

**Consistent error shape:**

```json
{
  "detail": {
    "message": "Customer abc123 not found",
    "code": "NOT_FOUND"
  }
}
```

For validation errors, FastAPI returns 422 automatically with Pydantic field-level details. Override with a custom exception handler if you need a different format.

---

## Pagination

### Offset/Limit (Simple)

```python
@router.get("/")
async def list_customers(offset: int = 0, limit: int = 20):
    customers = operations.list_all(db, offset=offset, limit=limit)
    return {"data": customers, "offset": offset, "limit": limit}
```

**Pros:** Easy to implement, supports jumping to any page.
**Cons:** Inconsistent results if data changes between requests; slow for large offsets (DB must skip rows).

### Cursor-Based (Scalable)

```python
@router.get("/")
async def list_customers(cursor: str | None = None, limit: int = 20):
    customers, next_cursor = operations.list_paginated(db, cursor=cursor, limit=limit)
    return {"data": customers, "next_cursor": next_cursor}
```

**Pros:** Consistent results, performs well at any position.
**Cons:** Can't jump to arbitrary pages; cursor is opaque to the client.

Use offset/limit for admin dashboards and small datasets. Use cursor-based for public APIs and large datasets.

---

## OpenAPI / Swagger Documentation

FastAPI auto-generates OpenAPI docs from type hints and Pydantic models. Enhance with:

```python
@router.post("/", status_code=201, response_model=Customer, summary="Create a customer")
async def create_customer(data: CustomerCreate):
    """Create a new customer with name and email. Returns the created customer with generated ID."""
    return operations.create(data.model_dump(), db)
```

- **`response_model`** — documents (and filters) the response schema
- **`summary`** — short description in the endpoint list
- **Docstring** — detailed description in the expanded view
- **`tags`** on the router — groups endpoints in the sidebar

Access at `/docs` (Swagger UI) or `/redoc` (ReDoc).

---

## Versioning

Prefer URL path versioning for simplicity:

```python
app.include_router(customers_v1.router, prefix="/v1")
app.include_router(customers_v2.router, prefix="/v2")
```

Alternative: header-based versioning (`Accept: application/vnd.api+json;version=2`). More RESTful but harder for clients to use and test.

**Rule:** Only introduce a new version when making breaking changes. Non-breaking additions (new optional fields, new endpoints) don't require a version bump.

---

## Metadata Pattern

Return a `metadata` dictionary alongside resource data for computed or derived information:

```python
@router.get("/{booking_id}")
async def get_booking(booking_id: str):
    booking = operations.get_by_id(booking_id, db)
    return {
        **booking,
        "metadata": {
            "total_price": compute_total(booking),
            "nights": compute_nights(booking),
            "is_refundable": booking["check_in"] > datetime.now(),
        },
    }
```

This keeps the core resource clean while providing useful derived values. The client knows `metadata` fields are computed, not stored.

---

## Relationship to Architecture Layers

```
Client  →  Router (REST conventions)  →  Operations (business logic)  →  Database
```

- **Router** enforces REST conventions: HTTP methods, status codes, URL naming, pagination parameters, error response format
- **Operations** contain business rules and don't know about HTTP
- **Database** handles persistence and doesn't know about REST

See `layered-architecture.md` for the full three-layer architecture. See `error-handling.md` for exception-to-HTTP-status mapping patterns.
