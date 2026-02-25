# Async Patterns

How to write async Python code for FastAPI applications. Covers coroutines, concurrent execution, async context managers, async generators, and the async database access patterns that FastAPI projects need.

> Content inspired by Arjan Codes' asyncio deep-dive examples.

---

## 1. Core Concepts

### Coroutines

A function defined with `async def` returns a coroutine. Calling it does not execute the body — you must `await` it.

```python
async def fetch_user(user_id: str) -> dict:
    # This runs when awaited, not when called
    return await db.read_by_id(user_id)
```

### The Event Loop

`asyncio.run()` creates an event loop and runs a coroutine to completion. FastAPI manages its own loop — you never call `asyncio.run()` inside a route handler.

```python
# Standalone script
async def main() -> None:
    result = await fetch_user("user-1")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

```python
# FastAPI route — no asyncio.run() needed
@router.get("/users/{user_id}")
async def get_user(user_id: str):
    return await fetch_user(user_id)
```

### When to Use async def vs def in FastAPI

FastAPI handles both `async def` and plain `def` route handlers:

- **`async def`** — Use when the handler calls async I/O (database, HTTP client, file I/O). The handler runs on the main event loop.
- **`def`** — Use when the handler does only CPU-bound or synchronous work. FastAPI runs it in a thread pool automatically.

```python
# Async handler — calls async database
@router.get("/users/{user_id}")
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one()

# Sync handler — CPU-bound computation
@router.post("/reports")
def generate_report(data: ReportRequest):
    return compute_report(data)  # synchronous, runs in thread pool
```

---

## 2. Concurrent Execution

### asyncio.gather()

Run multiple coroutines concurrently and collect all results. Use when you have independent I/O operations that don't depend on each other.

```python
import asyncio

async def fetch_user(user_id: str) -> dict: ...
async def fetch_orders(user_id: str) -> list[dict]: ...
async def fetch_preferences(user_id: str) -> dict: ...

async def get_user_dashboard(user_id: str) -> dict:
    # All three run concurrently — total time ≈ slowest call, not sum of all
    user, orders, prefs = await asyncio.gather(
        fetch_user(user_id),
        fetch_orders(user_id),
        fetch_preferences(user_id),
    )
    return {"user": user, "orders": orders, "preferences": prefs}
```

### asyncio.TaskGroup (Python 3.11+)

Structured concurrency — if any task fails, all others are cancelled. Preferred over `gather()` when you need all tasks to succeed.

```python
async def initialize_tables() -> None:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(create_table("users"))
        tg.create_task(create_table("orders"))
        tg.create_task(create_table("products"))
    # All tables created, or all cancelled if one failed
```

### When to Use Each

| Approach | Use when... |
|---|---|
| `await` sequentially | Results depend on each other (second call needs first result) |
| `asyncio.gather()` | Independent calls; partial success is acceptable |
| `asyncio.TaskGroup()` | Independent calls; all-or-nothing semantics needed |

---

## 3. Async Context Managers

### Writing Async Context Managers

The async version of `__enter__`/`__exit__` uses `__aenter__`/`__aexit__`:

```python
class AsyncDatabaseConnection:
    def __init__(self, url: str):
        self.url = url
        self.connection = None

    async def __aenter__(self):
        self.connection = await connect(self.url)
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.connection.close()
        return False

# Usage
async with AsyncDatabaseConnection("postgresql://...") as conn:
    result = await conn.execute("SELECT * FROM users")
```

### @asynccontextmanager Decorator

For simpler cases, use the decorator from `contextlib`:

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    session = AsyncSession(engine)
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

### FastAPI Lifespan

FastAPI uses an async context manager for startup/shutdown logic:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables, warm caches, open connections
    await create_tables()
    yield
    # Shutdown: close connections, flush buffers
    await close_database()

app = FastAPI(lifespan=lifespan)
```

---

## 4. Async Generators

Use `async def` with `yield` to create async iterators. Useful for streaming results or processing data in chunks.

```python
from typing import AsyncIterable

async def fetch_pages(url: str) -> AsyncIterable[dict]:
    page = 1
    while True:
        data = await http_get(f"{url}?page={page}")
        if not data["results"]:
            break
        yield data
        page += 1

# Consume with async for
async def process_all_pages(url: str) -> list[dict]:
    results = []
    async for page in fetch_pages(url):
        results.extend(page["results"])
    return results

# Async list comprehension
async def get_all_names(url: str) -> list[str]:
    return [item["name"] async for page in fetch_pages(url) for item in page["results"]]
```

---

## 5. Async Database Access

### SQLAlchemy AsyncSession

The standard pattern for async database access in FastAPI:

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
```

### Async DataInterface

Extend the three-layer architecture's DataInterface for async operations:

```python
from typing import Any, Protocol

DataObject = dict[str, Any]

class AsyncDataInterface(Protocol):
    async def read_by_id(self, id: str) -> DataObject: ...
    async def read_all(self) -> list[DataObject]: ...
    async def create(self, data: DataObject) -> DataObject: ...
    async def update(self, id: str, data: DataObject) -> DataObject: ...
    async def delete(self, id: str) -> None: ...
```

### Async Operations Layer

```python
async def create_booking(
    data: BookingCreate,
    booking_db: AsyncDataInterface,
    room_db: AsyncDataInterface,
) -> Booking:
    room = await room_db.read_by_id(data.room_id)
    nights = (data.to_date - data.from_date).days
    price = nights * room["price"]
    booking_data = {**data.model_dump(), "id": str(uuid4()), "price": price}
    created = await booking_db.create(booking_data)
    return Booking(**created)
```

### Async DBInterface Implementation

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class AsyncDBInterface:
    def __init__(self, session: AsyncSession, model):
        self.session = session
        self.model = model

    async def read_by_id(self, id: str) -> DataObject:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise KeyError(f"Not found: {id}")
        return row.to_dict()

    async def read_all(self) -> list[DataObject]:
        result = await self.session.execute(select(self.model))
        return [row.to_dict() for row in result.scalars().all()]

    async def create(self, data: DataObject) -> DataObject:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance.to_dict()

    async def update(self, id: str, data: DataObject) -> DataObject:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        instance = result.scalar_one_or_none()
        if instance is None:
            raise KeyError(f"Not found: {id}")
        for key, value in data.items():
            setattr(instance, key, value)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance.to_dict()

    async def delete(self, id: str) -> None:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        instance = result.scalar_one_or_none()
        if instance is None:
            raise KeyError(f"Not found: {id}")
        await self.session.delete(instance)
        await self.session.commit()
```

---

## 6. Testing Async Code

### Async DataInterfaceStub

```python
class AsyncDataInterfaceStub:
    def __init__(self):
        self.data: dict[str, DataObject] = {}

    async def read_by_id(self, id: str) -> DataObject:
        if id not in self.data:
            raise KeyError(f"Not found: {id}")
        return self.data[id]

    async def read_all(self) -> list[DataObject]:
        return list(self.data.values())

    async def create(self, data: DataObject) -> DataObject:
        self.data[data["id"]] = data
        return data

    async def update(self, id: str, data: DataObject) -> DataObject:
        if id not in self.data:
            raise KeyError(f"Not found: {id}")
        self.data[id].update(data)
        return self.data[id]

    async def delete(self, id: str) -> None:
        if id not in self.data:
            raise KeyError(f"Not found: {id}")
        del self.data[id]
```

### pytest-asyncio

Use `@pytest.mark.asyncio` to test async functions:

```python
import pytest

@pytest.mark.asyncio
async def test_create_booking_computes_price():
    room_stub = AsyncDataInterfaceStub()
    room_stub.data["room-1"] = {"id": "room-1", "price": 100}

    booking_stub = AsyncDataInterfaceStub()
    data = BookingCreate(
        room_id="room-1",
        from_date=date(2024, 1, 1),
        to_date=date(2024, 1, 4),
    )
    booking = await create_booking(data, booking_stub, room_stub)
    assert booking.price == 300
```

---

## 7. Common Mistakes

| Mistake | Problem | Fix |
|---|---|---|
| Calling `asyncio.run()` inside FastAPI | Creates nested event loop, crashes | Just `await` directly |
| Using `time.sleep()` in async code | Blocks the entire event loop | Use `await asyncio.sleep()` |
| Sequential awaits for independent calls | No concurrency benefit | Use `asyncio.gather()` |
| Mixing sync DB driver with async handler | Blocks event loop during queries | Use async driver (`asyncpg`, `aiosqlite`) |
| Forgetting `await` on a coroutine | Returns coroutine object instead of result | Always `await` async calls |
| Using sync file I/O in async code | Blocks event loop | Use `aiofiles` or run in executor |
