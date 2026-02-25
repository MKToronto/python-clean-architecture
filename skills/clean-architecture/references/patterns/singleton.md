# Singleton

The class-based Singleton pattern is an anti-pattern in Python. If you need a single shared resource, the preferred approach is **dependency injection** — pass the resource as an explicit parameter and create it in the composition root. When DI creates too much parameter-passing overhead, a module-level instance is an acceptable fallback.

---

## Historical Context

The Singleton pattern originated in Java/C++, where you cannot have module-level instances — everything must live in a class. Python's module system makes this unnecessary. A Python module is itself a singleton (imported once and cached by the runtime). When you see "use the Singleton pattern," in Python think "create a module-level instance" or "inject the dependency."

---

## The Problem

Some resources should exist exactly once: configuration, database connection pools, ML model loaders, loggers. Creating multiple instances wastes memory or causes conflicts.

---

## Preferred Approach: Dependency Injection

Pass the shared resource as an explicit parameter. Create it once in the composition root (`main()` or the router layer in FastAPI).

```python
# config.py
@dataclass
class Config:
    db_uri: str = "sqlite:///:memory:"
    debug: bool = True

# main.py — composition root
def main() -> None:
    config = Config()
    service = create_service(config)
    service.run()
```

This keeps dependencies visible, testable, and swappable. No global state, no hidden coupling.

---

## Fallback: Module-Level Instance

When DI creates too much parameter-passing overhead, a module-level instance is simpler than a class-based singleton. Python modules are imported once and cached:

```python
# config.py
db_uri = "sqlite:///:memory:"
debug = True
```

```python
# anywhere in the codebase
import config

if config.debug:
    print(config.db_uri)
```

Every import of `config` gets the same module object. No metaclass, no `__new__` override, no ceremony.

**Advantages over class-based singleton:**
- Leverages Python's built-in module caching
- Explicit and readable
- Thread-safe by default
- No surprising behavior

**Still has drawbacks:** This is still global state. Functions that access the module have hidden dependencies that don't appear in their signatures, making them harder to test and reason about. Whenever you reach for this, first check whether you can pass the resource as a parameter instead.

---

## Metaclass Approach (When You Need It)

When you need a class with methods/properties but want exactly one instance, use a metaclass:

```python
class Singleton(type):
    _instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
```

```python
class Config(metaclass=Singleton):
    def __init__(self):
        self.db_url = "sqlite:///:memory:"
        self.debug = True

s1 = Config()
s2 = Config()
print(s1 is s2)  # True — same instance
```

### Thread-Safe Variant

The basic metaclass is not thread-safe. For multi-threaded applications, add double-checked locking:

```python
import threading
from typing import Any


class Singleton(type):
    _instances: dict[type, Any] = {}
    _locks: dict[type, threading.Lock] = {}
    _global_lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        # Fast path: already created
        if cls in cls._instances:
            return cls._instances[cls]

        # Ensure a per-class lock exists
        with cls._global_lock:
            lock = cls._locks.setdefault(cls, threading.Lock())

        # Double-checked locking: only one thread creates the instance
        with lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)

        return cls._instances[cls]
```

---

## `__new__` Override (Alternative)

A simpler but less reusable approach — override `__new__` on the class itself:

```python
class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.db_url = "sqlite:///:memory:"
        self.debug = True
```

**Caution:** `__init__` runs every time `Config()` is called, which may reset attributes. The metaclass approach avoids this because it short-circuits before `__init__`.

---

## Which Approach to Use

| Approach | Use when... |
|---|---|
| **Dependency injection** | Always preferred — pass the resource as a parameter, create in composition root |
| Module-level instance | DI creates excessive parameter-passing overhead; resource is truly global (logging config) |
| Metaclass singleton | Need a class with methods AND controlled instantiation (rare) |
| `__new__` override | Quick one-off, don't need reusable pattern (rare) |

---

## Why Class-Based Singletons Are an Anti-Pattern

Singletons are global state in disguise. They create the same problems as global coupling (the 2nd worst coupling type — see `references/design-principles.md`):

- **Hidden dependencies** — functions use the singleton without declaring it as a parameter
- **Hard to test** — can't easily substitute a different instance per test
- **Tight coupling** — every consumer is coupled to a specific implementation
- **Thread safety issues** — basic implementations have race conditions in multi-threaded code
- **Breaks inheritance** — subclasses can create additional instances, defeating the purpose

Module-level instances avoid the class-based pitfalls but still introduce global state. The hierarchy of preference is:

1. **Best:** Dependency injection — pass resources as parameters
2. **Acceptable fallback:** Module-level instance when DI is impractical
3. **Avoid:** Class-based Singleton pattern (metaclass or `__new__`)

```python
# BEST: explicit dependency
def process_order(order: Order, config: Config) -> None: ...

# ACCEPTABLE: module-level (still global state)
import config
def process_order(order: Order) -> None:
    if config.debug: ...

# AVOID: class-based singleton (hidden dependency)
def process_order(order: Order) -> None:
    config = Config()  # hidden singleton access
```

---

## Object Pool Variant

When the cost of creating objects is high but you need more than one instance, use an **object pool** — a bounded collection of reusable instances. This is common for database connections and thread pools:

```python
from queue import Queue

class ConnectionPool:
    def __init__(self, max_size: int, factory: Callable[[], Connection]):
        self._pool: Queue[Connection] = Queue(maxsize=max_size)
        for _ in range(max_size):
            self._pool.put(factory())

    def acquire(self) -> Connection:
        return self._pool.get()

    def release(self, conn: Connection) -> None:
        self._pool.put(conn)
```

SQLAlchemy's `create_engine()` creates a connection pool internally. FastAPI's `Depends(get_db)` acquires and releases connections from this pool per-request.

---

## Trade-offs

| Advantage | Cost |
|---|---|
| Guarantees single instance | Global state — hard to test if overused |
| Lazy initialization (created on first use) | Thread safety requires extra work (metaclass/`__new__`) |
| Shared resource management | Hidden dependencies if accessed directly |
| Module-level avoids class ceremony | Still introduces global coupling |
