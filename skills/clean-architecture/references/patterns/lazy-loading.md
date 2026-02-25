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

## `functools.cached_property` for Class Attributes

Computes an attribute on first access and caches it on the instance:

```python
from functools import cached_property

class DataPipeline:
    def __init__(self, config_path: str) -> None:
        self.config_path = config_path

    @cached_property
    def config(self) -> dict:
        """Loaded only when first accessed."""
        with open(self.config_path) as f:
            return json.load(f)

    @cached_property
    def model(self) -> Model:
        """Loaded only when first accessed."""
        return Model.from_pretrained(self.config["model_name"])
```

**Note:** `@cached_property` requires the class to be mutable (not frozen). It works by storing the result as an instance attribute that shadows the descriptor.

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

## `__getattr__` for Deferred Attribute Initialization

Load attributes on first access using Python's attribute lookup protocol:

```python
class LazyConfig:
    def __init__(self, config_path: str) -> None:
        self._config_path = config_path
        self._loaded: dict[str, Any] = {}

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._loaded:
            # Load from config file on first access
            with open(self._config_path) as f:
                data = json.load(f)
            self._loaded = data
        return self._loaded[name]
```

**How it works:** `__getattr__` is only called when normal attribute lookup fails. Once you set the attribute on the instance (via `self.__dict__`), `__getattr__` is never called again for that name.

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
@app.on_event("startup")
async def startup():
    start_preloading()

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

## When NOT to Use

- **Small, fast resources** — lazy loading adds complexity for negligible savings
- **Resources always needed** — if every request uses it, eager loading is simpler
- **Deterministic startup** — when you need to fail fast on missing resources
- **Thread-unsafe resources** — lazy initialization needs synchronization in multi-threaded code

## Relationship to Other Patterns

- **Singleton** (`patterns/singleton.md`) — module-level lazy instance is both a singleton and lazy loading
- **Facade** (`patterns/facade.md`) — a facade can lazily initialize subsystem components
- **Registry** (`patterns/registry.md`) — plugin registry can use lazy loading for plugin discovery
