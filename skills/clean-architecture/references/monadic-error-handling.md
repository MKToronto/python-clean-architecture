# Monadic Error Handling (Railway-Oriented Programming)

An alternative to Python's exception-based error handling that makes errors explicit in the return type. Instead of try/except with hidden control flow, functions return `Result` containers that carry either a success value or a failure value — like two parallel railway tracks.

> **Note:** This is an advanced functional programming technique. For most Python/FastAPI projects, the standard approach in `error-handling.md` (custom exceptions + context managers + layered catch boundaries) is simpler and more idiomatic. Use monadic error handling when you need explicit error tracking through a chain of operations.

---

## The Problem with Exceptions

Exceptions create **hidden control flow**. When a function raises, execution jumps to an unknown catch site. The function signature doesn't reveal that it can fail:

```python
def fetch_blog(blog_id: str) -> Blog:  # signature says it returns Blog
    # ...but it might raise NotFoundError or NotAuthorizedError
    # the caller has no way to know without reading the implementation
```

This leads to:
- Forgetting to handle an exception (silent bugs)
- Catching too broadly (`except Exception:`) which hides real bugs
- Resource cleanup complexity (need `finally` or context managers)

---

## Railway-Oriented Programming

Instead of raising exceptions, every function returns a **Result** container with two tracks:

- **Success track** — contains the computed value
- **Failure track** — contains the error

As long as everything succeeds, data flows along the success track. The moment something fails, it switches to the failure track and the remaining functions are bypassed.

```
Input → [fn1] → [fn2] → [fn3] → Success(result)
                   ↓
              Failure(error) ────────→ Failure(error)
```

---

## Implementation with `returns` Library

The [`returns`](https://github.com/dry-python/returns) library (part of DryPython) provides the building blocks.

### The `@safe` Decorator

Converts a function that may raise into one that returns a `Result`:

```python
from returns.result import safe

@safe
def fetch_blog_from_db(blog_id: str) -> dict:
    connection = sqlite3.connect("application.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM blogs WHERE id = ?", (blog_id,))
    result = cursor.fetchone()
    if result is None:
        raise NotFoundError(f"Blog not found: {blog_id}")
    return result

# Without @safe: raises NotFoundError
# With @safe: returns Failure(NotFoundError(...)) or Success(dict)
```

### The `flow` Function

Chains operations into a pipeline. Each function receives the output of the previous one:

```python
from returns.pipeline import flow
from returns.pointfree import bind

def fetch_blog(blog_id: str) -> Result:
    return flow(
        blog_id,
        fetch_blog_from_db,       # str → Result[dict, Exception]
        bind(blog_to_dict),        # dict → Result[dict, Exception]
        bind(verify_access),       # dict → Result[Blog, Exception]
    )
```

### The `bind` Function

Adapts a `@safe` function to accept a `Result` as input instead of a raw value. If the input is a `Failure`, `bind` short-circuits — the function is never called, and the `Failure` passes through.

```python
@safe
def blog_to_dict(row: tuple) -> dict:
    return {"id": row[0], "title": row[1], "content": row[2], "public": row[3]}

@safe
def verify_access(blog: dict) -> dict:
    if not blog.get("public"):
        raise NotAuthorizedError(f"Access denied: {blog['id']}")
    return blog
```

### Handling the Result

```python
result = fetch_blog("first-blog")

# Pattern match on the result
match result:
    case Success(blog):
        print(f"Found blog: {blog['title']}")
    case Failure(NotFoundError() as e):
        print(f"404: {e}")
    case Failure(NotAuthorizedError() as e):
        print(f"403: {e}")
    case Failure(error):
        print(f"500: Unexpected error: {error}")
```

---

## Comparison: Exceptions vs Railway

### Exception-based (standard Python)

```python
def fetch_blog(blog_id: str) -> Blog:
    with SQLite() as cursor:
        cursor.execute("SELECT * FROM blogs WHERE id = ?", (blog_id,))
        result = cursor.fetchone()
    if result is None:
        raise NotFoundError(f"Blog not found: {blog_id}")
    blog = result_to_blog(result)
    if not blog.public:
        raise NotAuthorizedError(f"Access denied: {blog_id}")
    return blog

# Caller must know to catch NotFoundError and NotAuthorizedError
try:
    blog = fetch_blog(blog_id)
except NotFoundError:
    return 404
except NotAuthorizedError:
    return 403
```

### Railway-oriented (monadic)

```python
def fetch_blog(blog_id: str) -> Result[Blog, Exception]:
    return flow(
        blog_id,
        fetch_blog_from_db,
        bind(blog_to_dict),
        bind(verify_access),
    )

# Caller sees Result in the return type — errors are explicit
result = fetch_blog(blog_id)
# Handle Success/Failure explicitly
```

---

## Advantages

- **No hidden control flow** — errors are values, not jumps. The function signature tells you it can fail.
- **Composable** — `flow` + `bind` let you chain operations cleanly; a failure at any step short-circuits the rest.
- **Explicit handling** — you must deal with the `Result`; you can't accidentally forget to catch an exception.
- **Works with pattern matching** — Python 3.10+ `match`/`case` handles `Success`/`Failure` cleanly.

## Disadvantages

- **Not idiomatic Python** — most Python libraries raise exceptions; wrapping everything in `@safe` is friction.
- **Third-party dependency** — requires the `returns` library (not in the standard library).
- **Team familiarity** — functional error handling is unfamiliar to most Python developers.
- **Type checker support** — `partial` and `flow` type inference is imperfect in mypy/pyright.

---

## When to Use

- **Complex pipelines** with many sequential operations where any step can fail — data processing, multi-step validation, ETL
- **When you want error tracking through composition** — each step's error propagates without try/except nesting
- **Functional codebases** that already use `functools.reduce`, `partial`, and pipeline patterns

## When NOT to Use

- **Standard FastAPI endpoints** — the exception-based approach in `error-handling.md` with layered catch boundaries is simpler and more idiomatic
- **Simple error cases** — if you have one or two failure modes, custom exceptions are clearer
- **Team unfamiliar with FP** — the abstraction overhead isn't worth it if the team finds it confusing

## Relationship to Other Patterns

- **Pipeline** (`patterns/pipeline.md`) composes pure functions with `functools.reduce`. Monadic error handling adds failure tracking to pipelines.
- **Error Handling** (`error-handling.md`) covers the standard exception-based approach. Monadic error handling is a functional alternative, not a replacement.
- **Context Managers** still handle resource cleanup even in railway-oriented code — `@safe` wraps exceptions but doesn't replace `with` statements.
