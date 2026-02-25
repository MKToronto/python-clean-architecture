# Singleton

Ensure a class has only one instance. In Python, the preferred approach is the module-level instance — Python's module system is a natural singleton mechanism.

---

## The Problem

Some resources should exist exactly once: configuration, database connection pools, ML model loaders, loggers. Creating multiple instances wastes memory or causes conflicts.

---

## Pythonic Approach: Module-Level Instance (Preferred)

Python modules are imported once and cached. A module-level instance is the simplest singleton:

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

**Why this is best:**
- Leverages Python's built-in module caching
- Explicit and readable
- Easy to test (mock the module or its attributes)
- No surprising behavior

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
| Module-level instance | Configuration, simple shared state — the default choice |
| Metaclass singleton | Need class with methods AND exactly one instance |
| Thread-safe metaclass | Multi-threaded application with metaclass singleton |
| `__new__` override | Quick one-off, don't need reusable pattern |

---

## Anti-Pattern Warning

Singletons are global state in disguise. Overuse creates the same problems as global coupling:

- Hidden dependencies (functions use singleton without declaring it as a parameter)
- Hard to test (can't easily substitute a different instance)
- Tight coupling to a specific implementation

**Prefer dependency injection:** Pass the shared resource as a parameter. Use singleton only for truly global resources (config, logging) that don't need to be swapped in tests.

```python
# Prefer this (explicit dependency)
def process_order(order: Order, config: Config) -> None: ...

# Over this (hidden singleton access)
def process_order(order: Order) -> None:
    config = Config()  # hidden dependency
```

---

## Trade-offs

| Advantage | Cost |
|---|---|
| Guarantees single instance | Global state — hard to test if overused |
| Lazy initialization (created on first use) | Thread safety requires extra work |
| Shared resource management | Hidden dependencies if accessed directly |
