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

## Sensible Defaults

Design query parameters with defaults that minimize required input. The goal is to make the common case require the fewest arguments.

```python
from datetime import datetime, timedelta

@router.get("/transactions")
async def list_transactions(
    start_date: datetime = Query(default_factory=lambda: datetime.now() - timedelta(days=1)),
    end_date: datetime = Query(default_factory=datetime.now),
    limit: int = Query(default=20, ge=1, le=100),
):
    ...
```

Anti-pattern: requiring arguments that have obvious defaults (e.g., forcing the caller to pass `end_date=now` every time). If `end_date` is almost always "right now," default it to that.

Use `Query()` constraints (`ge`, `le`, `min_length`, `max_length`) directly on endpoint parameters to add validation without separate Pydantic models for simple query parameters:

```python
@router.get("/convert")
async def convert(
    from_currency: str = Query(min_length=3, max_length=3),
    to_currency: str = Query(min_length=3, max_length=3),
    amount: Decimal = Query(gt=0),
):
    ...
```

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

### Response Descriptions per Status Code

Use the `responses` parameter on endpoints to document what each status code means:

```python
@router.post(
    "/",
    status_code=201,
    response_model=Customer,
    responses={
        400: {"description": "Customer with this email already exists"},
        422: {"description": "Validation error in request body"},
    },
)
async def create_customer(data: CustomerCreate):
    ...
```

FastAPI renders these in both `/docs` and `/redoc`. Combine with `summary` and docstrings for complete endpoint documentation.

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

## Health Check Endpoint

Every production API needs a health endpoint that infrastructure (Kubernetes, load balancers) can poll:

```python
@router.get("/health")
async def health():
    return {"status": "ok"}
```

Keep this lightweight and free of authentication. For deeper checks (database connectivity, external service availability), add a separate `/health/detailed` endpoint behind authentication.

---

## Rate Limiting

Rate limiting controls how many requests a client can make within a time window. It prevents abuse, protects against brute-force attacks, and manages cost for usage-based APIs.

### SlowAPI Integration

```bash
pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Try again later."},
    )
```

### Per-Endpoint Limits

Apply different limits to different endpoints. Write operations typically need stricter limits:

```python
@router.get("/{item_id}")
@limiter.limit("10/second")
async def read_item(request: Request, item_id: str):
    ...

@router.post("/")
@limiter.limit("1/second")
async def create_item(request: Request, data: ItemCreate):
    ...
```

The `@limiter.limit()` decorator must come AFTER (below) the `@router` decorator. The endpoint must accept a `request: Request` parameter.

### Burst Handling with Multiple Limits

Combine a permissive short-window limit with a stricter long-window limit:

```python
@router.get("/")
@limiter.limit("10/second")
@limiter.limit("120/minute")
async def list_items(request: Request):
    ...
```

### Rate Limiting by API Key

For per-user limits (e.g., free vs paid tiers), extract the API key from headers:

```python
def get_api_key(request: Request) -> str:
    return request.headers.get("x-api-key", "anonymous")

limiter = Limiter(key_func=get_api_key)
```

### Operational Considerations

- **Make limits configurable** via environment variables so they can change without redeploying
- **Multi-instance awareness** — in-memory rate limiting doesn't work across multiple API instances. Use Redis:

```python
limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")
```

---

## Relationship to Architecture Layers

```
Client  →  Router (REST conventions)  →  Operations (business logic)  →  Database
```

- **Router** enforces REST conventions: HTTP methods, status codes, URL naming, pagination parameters, error response format
- **Operations** contain business rules and don't know about HTTP
- **Database** handles persistence and doesn't know about REST

See `layered-architecture.md` for the full three-layer architecture. See `error-handling.md` for exception-to-HTTP-status mapping patterns.
