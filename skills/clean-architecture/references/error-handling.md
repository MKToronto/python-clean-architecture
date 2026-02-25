# Error Handling Reference

Handle errors precisely. Catch only what you can act on, let everything else propagate, and use context managers to guarantee resource cleanup. Content inspired by Arjan Codes' Software Designer Mindset course.

## 1. Custom Exception Classes

Define domain-specific exceptions that describe exactly what went wrong. Never raise generic `Exception` or `ValueError` for domain logic.

```python
class NotFoundError(Exception):
    """Raised when a requested entity does not exist."""
    pass


class NotAuthorizedError(Exception):
    """Raised when access to a resource is denied."""
    pass
```

Raise these exceptions at the point where the error is detected, inside the business logic layer:

```python
def fetch_blog(blog_id: str) -> Blog:
    connection = sqlite3.connect("application.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM blogs WHERE id = ?", (blog_id,))
    result = cursor.fetchone()
    connection.close()

    if result is None:
        raise NotFoundError(f"Blog not found: {blog_id}")

    blog = result_to_blog(result)

    if not blog.public:
        raise NotAuthorizedError(f"Access denied: {blog_id}")

    return blog
```

Custom exceptions provide two advantages over generic ones: they produce clear error messages that pinpoint the problem, and they let callers catch specific failure modes independently.

---

## 2. Try-Except Blocks

Catch specific exception types. Use multiple `except` clauses when different errors require different responses.

```python
def get_blog_endpoint(blog_id: str):
    try:
        blog = fetch_blog(blog_id)
        print(blog)
    except NotFoundError:
        print("Returning status code 404")
    except NotAuthorizedError:
        print("Returning status code 403")
```

Each `except` clause handles one failure mode. The caller decides how to respond to each error -- the business logic only raises them.

---

## 3. Anti-Patterns

### Never use bare `except:`

A bare `except:` catches everything, including `NameError`, `AttributeError`, `SyntaxError`, and `KeyboardInterrupt`. It silently swallows actual bugs in your code.

```python
# DANGEROUS: hides real bugs
try:
    something  # NameError -- this is a typo, not an expected error
except:
    pass  # silently swallowed, program continues with hidden bug
```

### Avoid `except Exception:`

Marginally better than bare `except:`, but still catches far too many error types. It masks bugs like `NameError` and `AttributeError` that indicate broken code, not runtime conditions.

```python
# BAD: catches everything that inherits from Exception
try:
    blog = fetch_blog(blog_id)
except Exception:
    return 404  # a typo in fetch_blog also returns 404
```

### Do not catch what you cannot handle

If you have no meaningful recovery action, do not catch the exception. Let it propagate. A crashed application with a clear traceback is better than a silently broken one.

```python
# BAD: catching with no useful action
try:
    result = complex_calculation()
except ValueError:
    pass  # now result is undefined, problems will surface later

# GOOD: let it propagate
result = complex_calculation()  # crashes with clear traceback if broken
```

### Do not scatter try-except everywhere

Wrapping every function call in try-except complicates control flow and obscures the real logic. Catch exceptions at defined boundaries (API endpoints, CLI entry points), not inside every function.

---

## 4. The Finally Block

The `finally` block runs whether or not an exception occurred. Use it to guarantee cleanup of resources that were acquired before the error.

```python
def fetch_blog(blog_id: str) -> Blog:
    connection = sqlite3.connect("application.db")
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM blogs WHERE id = ?", (blog_id,))
        result = cursor.fetchone()

        if result is None:
            raise NotFoundError(f"Blog not found: {blog_id}")

        blog = result_to_blog(result)

        if not blog.public:
            raise NotAuthorizedError(f"Access denied: {blog_id}")

        return blog
    finally:
        print("Closing connection")
        connection.close()
```

Without `finally`, an exception raised after `connect()` but before `close()` leaves the connection open. The `finally` block guarantees `connection.close()` runs regardless of whether the function returns normally or raises.

The problem with `try/finally` is that it clutters the function with resource management details. Context managers solve this.

---

## 5. Context Managers (Preferred)

A context manager encapsulates resource acquisition and cleanup into a reusable object. It implements `__enter__` (setup) and `__exit__` (teardown). The `__exit__` method runs even if an exception occurs inside the `with` block -- the same guarantee as `finally`, but in a self-contained, reusable form.

### Complete database connection context manager

```python
import sqlite3


class SQLite:
    def __init__(self, file: str = "application.db"):
        self.file = file
        self.connection: sqlite3.Connection | None = None

    def __enter__(self) -> sqlite3.Cursor:
        self.connection = sqlite3.connect(self.file)
        return self.connection.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            print("Closing connection")
            self.connection.close()
```

The `__exit__` method checks whether a connection exists before closing it. If `sqlite3.connect()` fails inside `__enter__`, `self.connection` stays `None` and `__exit__` skips the close call.

### Using the context manager

```python
def fetch_blog(blog_id: str) -> Blog:
    with SQLite("application.db") as cursor:
        cursor.execute("SELECT * FROM blogs WHERE id = ?", (blog_id,))
        result = cursor.fetchone()

    if result is None:
        raise NotFoundError(f"Blog not found: {blog_id}")

    blog = result_to_blog(result)

    if not blog.public:
        raise NotAuthorizedError(f"Access denied: {blog_id}")

    return blog
```

Compare this to the `try/finally` version. The function now focuses entirely on business logic. Resource management is delegated to `SQLite`, which is reusable across every function that touches the database.

### Why context managers are superior to try-finally

- **Reusable** -- define cleanup once, use it everywhere
- **Self-contained** -- initialization and cleanup live together in one class
- **Composable** -- nest multiple `with` blocks or use `contextlib.ExitStack`
- **Pythonic** -- the `with` statement is the standard idiom for resource management

---

## 6. Error Handling Layers

Structure error handling across architectural layers. Each layer has a specific responsibility.

### Business logic layer: raise domain exceptions

```python
# operations/blogs.py

def fetch_blog(blog_id: str) -> Blog:
    with SQLite("application.db") as cursor:
        cursor.execute("SELECT * FROM blogs WHERE id = ?", (blog_id,))
        result = cursor.fetchone()

    if result is None:
        raise NotFoundError(f"Blog not found: {blog_id}")

    blog = result_to_blog(result)

    if not blog.public:
        raise NotAuthorizedError(f"Access denied: {blog_id}")

    return blog
```

### API layer: catch and convert to HTTP responses

```python
# routers/blogs.py
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/blogs/{blog_id}")
def get_blog(blog_id: str):
    try:
        blog = fetch_blog(blog_id)
        return blog
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Blog not found")
    except NotAuthorizedError:
        raise HTTPException(status_code=403, detail="Access denied")
```

### Let unhandled exceptions propagate

Do not add a catch-all at the API layer. If an unexpected exception occurs (database corruption, network failure), let it surface as a 500 error with a full traceback in the server logs. This makes the problem visible rather than hiding it behind a misleading status code.

```python
# BAD: catch-all hides real problems
@router.get("/blogs/{blog_id}")
def get_blog(blog_id: str):
    try:
        blog = fetch_blog(blog_id)
        return blog
    except Exception:  # masks database errors, typos, everything
        raise HTTPException(status_code=500, detail="Something went wrong")
```

---

## 7. Python-Specific Caution

Python's dynamic typing makes broad exception catching especially dangerous. The interpreter uses exceptions internally during code execution. A bare `except:` or `except Exception:` catches errors that indicate genuine bugs in your code, not runtime conditions:

- **`NameError`** -- a variable name is misspelled or undefined
- **`AttributeError`** -- calling a method that does not exist on an object
- **`TypeError`** -- passing wrong argument types to a function
- **`SyntaxError`** -- (in dynamically evaluated code) malformed Python

These are programming errors. They should crash the program immediately with a clear traceback so you can fix them. Catching them silently means the bug persists and surfaces later in confusing, hard-to-debug ways.

```python
# This program has a bug (undefined variable), but runs without error
try:
    undefined_variable  # NameError: a real bug
except:
    pass  # bug is hidden, program continues in broken state
```

Linting tools like pylint and ruff flag bare `except:` clauses for exactly this reason.

---

## 8. Best Practices Summary

### Do

- Create custom exception classes for each domain error condition
- Use `@dataclass` exceptions that carry relevant context (IDs, names)
- Catch the most specific exception type possible
- Use multiple `except` clauses for different error types
- Use context managers for all resource lifecycle management (database connections, file handles, network sockets)
- Raise exceptions in business logic, catch them at the boundary (API, CLI)
- Let unexpected exceptions propagate with full tracebacks
- Use linting tools (ruff, pylint) to flag dangerous exception patterns

### Do Not

- Use bare `except:` -- it catches everything including bugs
- Use `except Exception:` -- nearly as bad, still catches `NameError` and `AttributeError`
- Catch exceptions you cannot meaningfully handle
- Use `except: pass` -- the most dangerous pattern in Python error handling
- Scatter try-except blocks throughout every function
- Return misleading status codes from catch-all handlers
- Use try-finally for resource cleanup when a context manager is an option
