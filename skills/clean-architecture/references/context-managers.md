# Context Managers Reference

Context managers guarantee cleanup of resources regardless of whether an operation succeeds or fails. They replace `try/finally` blocks with a reusable, composable pattern. Content inspired by Arjan Codes' Software Designer Mindset course.

## 1. The Problem: Manual Cleanup

Without context managers, resource cleanup requires `try/finally`:

```python
import sqlite3

def fetch_data(query: str) -> list[dict]:
    connection = sqlite3.connect("app.db")
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        connection.close()
```

This works but has problems: cleanup logic is mixed with business logic, it's not reusable, and nesting multiple resources creates deeply indented `try/finally` pyramids.

---

## 2. The `with` Statement

The `with` statement delegates setup and teardown to a context manager object. The object's `__enter__` runs at the start, and `__exit__` runs when the block ends — even if an exception is raised.

```python
with open("data.txt") as f:
    content = f.read()
# f.close() is called automatically, even if read() raises
```

---

## 3. Writing a Context Manager Class

Implement `__enter__` and `__exit__`. The `__enter__` method returns the resource. The `__exit__` method cleans it up.

```python
import sqlite3


class SQLite:
    def __init__(self, file: str = "app.db"):
        self.file = file
        self.connection: sqlite3.Connection | None = None

    def __enter__(self) -> sqlite3.Cursor:
        self.connection = sqlite3.connect(self.file)
        return self.connection.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.connection:
            self.connection.close()
```

Usage:

```python
def fetch_data(query: str) -> list[dict]:
    with SQLite("app.db") as cursor:
        cursor.execute(query)
        return cursor.fetchall()
    # connection is closed automatically
```

The function now contains only business logic. Resource management is delegated to `SQLite`, which is reusable wherever you need a database cursor.

### `__exit__` Parameters

`__exit__` receives three arguments describing any exception that occurred:

- `exc_type` — the exception class (e.g., `ValueError`), or `None` if no exception
- `exc_val` — the exception instance
- `exc_tb` — the traceback

If `__exit__` returns `True`, the exception is suppressed. If it returns `None` or `False` (the default), the exception propagates normally. Almost never suppress exceptions — let them propagate.

---

## 4. The `@contextmanager` Decorator

For simple context managers, writing a full class is verbose. The `contextlib.contextmanager` decorator turns a generator function into a context manager.

```python
from contextlib import contextmanager
import sqlite3
from typing import Iterator


@contextmanager
def sqlite_connection(file: str = "app.db") -> Iterator[sqlite3.Cursor]:
    connection = sqlite3.connect(file)
    try:
        yield connection.cursor()
    finally:
        connection.close()
```

Everything before `yield` is `__enter__`. The yielded value is what `with ... as` binds to. Everything after `yield` (in the `finally`) is `__exit__`.

```python
with sqlite_connection("app.db") as cursor:
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
```

### When to use class vs decorator

| Approach | Use when... |
|---|---|
| Class (`__enter__`/`__exit__`) | Context manager has state, needs configuration, or is complex |
| `@contextmanager` decorator | Simple setup/teardown, no persistent state needed |

---

## 5. Common Patterns

### File handling

```python
# Built-in — already a context manager
with open("output.txt", "w") as f:
    f.write("data")
```

### Database transactions

```python
@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Cursor]:
    cursor = connection.cursor()
    try:
        yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
```

### Temporary state changes

```python
@contextmanager
def temporary_setting(obj: object, attr: str, value: object) -> Iterator[None]:
    original = getattr(obj, attr)
    setattr(obj, attr, value)
    try:
        yield
    finally:
        setattr(obj, attr, original)
```

### Timing

```python
import time
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def timer(label: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"{label}: {elapsed:.3f}s")


with timer("query"):
    results = expensive_query()
```

---

## 6. Nesting and `ExitStack`

### Simple nesting

```python
with open("input.txt") as src, open("output.txt", "w") as dst:
    dst.write(src.read())
```

### Dynamic nesting with `ExitStack`

When the number of context managers is not known at write time, use `ExitStack`:

```python
from contextlib import ExitStack


def process_files(paths: list[str]) -> list[str]:
    with ExitStack() as stack:
        files = [stack.enter_context(open(p)) for p in paths]
        return [f.read() for f in files]
    # all files closed automatically
```

`ExitStack` collects context managers and calls their `__exit__` methods in reverse order when the block ends.

---

## 7. Async Context Managers

For async resources (database connections, HTTP sessions), implement `__aenter__` and `__aexit__`, or use `contextlib.asynccontextmanager`:

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator
import httpx


@asynccontextmanager
async def http_client() -> AsyncIterator[httpx.AsyncClient]:
    client = httpx.AsyncClient()
    try:
        yield client
    finally:
        await client.aclose()


async def fetch(url: str) -> str:
    async with http_client() as client:
        response = await client.get(url)
        return response.text
```

---

## 8. Best Practices

### Do

- Use context managers for all resource lifecycle management (files, connections, locks, sessions)
- Prefer `@contextmanager` for simple setup/teardown
- Use classes when the context manager needs configuration or state
- Use `ExitStack` when managing a dynamic number of resources
- Always put cleanup in `finally` inside `@contextmanager` generators

### Do Not

- Suppress exceptions in `__exit__` (returning `True`) unless you have a specific reason
- Use `try/finally` when a context manager would be reusable
- Forget to handle the case where `__enter__` fails (check for `None` in `__exit__`)
- Create context managers for trivial operations that don't need cleanup
