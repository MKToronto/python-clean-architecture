# REST API Design

Conventions and best practices for designing RESTful APIs with FastAPI. These guidelines complement the three-layer architecture in `layered-architecture.md` — they apply specifically to the Router layer.

---

## Resource Naming Conventions

- **Use plural nouns** for collections: `/customers`, `/orders`, `/rooms`
- **Use IDs for individual resources**: `/customers/{customer_id}`
- **Nest for relationships**: `/customers/{customer_id}/orders`

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

## Consistency

Use the same formats everywhere for dates, ranges, query parameters, error handling, and naming conventions. Make sure pagination works the same across all endpoints.

Use standard HTTP status codes. Provide a response body with additional information for errors. FastAPI returns 422 automatically for Pydantic validation errors.

---

## Pagination

Make pagination consistent across all list endpoints:

```python
@router.get("/")
async def list_customers(offset: int = 0, limit: int = 20):
    customers = operations.list_all(db, offset=offset, limit=limit)
    return {"data": customers, "offset": offset, "limit": limit}
```

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

Only introduce a new version when making breaking changes. Non-breaking additions (new optional fields, new endpoints) don't require a version bump.

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
