# Lazy Loading Pattern

**Recognize:** Application startup is slow because it loads all data, models, or resources upfront — even if many of them are never used in a given session.

**Problem:** Eager loading wastes time and memory on resources that may not be needed. This is especially painful for large datasets, ML models, optional features, and plugin systems.

---

## `functools.cache` for Computed-Once Properties

The simplest lazy loading — compute a value on first access, cache it forever:

```python
from functools import cache

@cache
def load_model(model_name: str) -> Model:
    print(f"Loading {model_name}...")  # only prints once
    return Model.from_pretrained(model_name)

# First call: loads model (slow)
model = load_model("bert-base")
# Second call: returns cached result (instant)
model = load_model("bert-base")
```

`@cache` is equivalent to `@lru_cache(maxsize=None)` — unbounded cache. For bounded caching, use `@lru_cache(maxsize=128)`.

---

## TTL Cache (Time-To-Live)

Cache results for a limited time — useful for data that changes periodically:

```python
import time
from functools import wraps
from typing import Callable, TypeVar

T = TypeVar("T")

def ttl_cache(ttl_seconds: float = 300) -> Callable:
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        cache: dict[tuple, tuple[T, float]] = {}

        @wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl_seconds:
                    return result
            result = fn(*args, **kwargs)
            cache[key] = (result, now)
            return result
        return wrapper
    return decorator

@ttl_cache(ttl_seconds=60)
def get_exchange_rate(currency: str) -> float:
    return requests.get(f"https://api.example.com/rate/{currency}").json()["rate"]
```

---

## Generators for Partial Data Loading

Process large datasets without loading everything into memory:

```python
from typing import Generator

def read_large_file(path: str, chunk_size: int = 1000) -> Generator[list[dict], None, None]:
    with open(path) as f:
        chunk = []
        for line in f:
            chunk.append(json.loads(line))
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk

# Process in chunks — never holds entire file in memory
for batch in read_large_file("events.jsonl"):
    process_batch(batch)
```

**Key insight:** Generators are Python's built-in lazy loading mechanism. Use `yield` to defer work until the consumer requests the next value.

---

## Background Preloading with Threading

Start loading resources in the background while the user interacts with the UI:

```python
import threading
from functools import cache

_preload_thread: threading.Thread | None = None

@cache
def load_model() -> Model:
    return Model.from_pretrained("large-model")

def start_preloading() -> None:
    global _preload_thread
    _preload_thread = threading.Thread(target=load_model, daemon=True)
    _preload_thread.start()

def get_model() -> Model:
    if _preload_thread is not None:
        _preload_thread.join()  # wait if still loading
    return load_model()  # returns cached result
```

**Usage in FastAPI:**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    start_preloading()
    yield

@app.get("/predict")
async def predict(text: str):
    model = get_model()  # instant if preload finished
    return {"result": model.predict(text)}
```

---

## When to Use

- **Large datasets** — load on demand or in chunks with generators
- **ML models** — defer loading until prediction is requested; preload in background
- **Optional features** — plugins or modules that many users never use
- **Configuration** — load config files only when settings are actually accessed
- **Database connections** — create connection pools lazily at first query

## Common Pitfalls

### Lazy Without Cache

Computing a value lazily but forgetting to cache the result. The expensive computation runs on every access:

```python
# BAD: lazy but not cached — reloads model every time
def get_model() -> Model:
    return Model.from_pretrained("large-model")  # expensive every call

# GOOD: @cache ensures it loads once
@cache
def get_model() -> Model:
    return Model.from_pretrained("large-model")
```

### Early Break with Generators

Generators only compute values as consumed. When you only need the first match, use `next()` or a loop with `break` — the remaining items are never computed:

```python
def find_first_match(items: Iterable[Item], predicate: Callable[[Item], bool]) -> Item | None:
    return next((item for item in items if predicate(item)), None)
```

This is especially powerful for large datasets where scanning everything would be wasteful.

### Caching Mutable Data

If the cached value is mutable (a list or dict), consumers can accidentally modify the shared cached copy:

```python
# DANGER: cached list is shared — mutations affect all callers
@cache
def get_settings() -> dict:
    return {"debug": True, "level": "INFO"}

settings = get_settings()
settings["debug"] = False  # modifies the cached copy!
```

Fix by returning frozen structures (`tuple`, `frozenset`, frozen dataclass) or by returning copies.

---

## When NOT to Use

- **Small, fast resources** — lazy loading adds complexity for negligible savings
- **Resources always needed** — if every request uses it, eager loading is simpler
- **Deterministic startup** — when you need to fail fast on missing resources
- **Thread-unsafe resources** — lazy initialization needs synchronization in multi-threaded code

## Relationship to Other Patterns

- **Singleton** (`singleton.md`) — module-level lazy instance is both a singleton and lazy loading
- **Facade** (`facade.md`) — a facade can lazily initialize subsystem components
- **Registry** (`registry.md`) — plugin registry can use lazy loading for plugin discovery
