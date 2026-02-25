# Adapter Pattern

**Recognize:** You need to use an existing library or system, but its interface doesn't match what your code expects.

**Problem:** Your application expects one interface (e.g., `dict.get(key)`) but the external system provides a different one (e.g., `BeautifulSoup.find(key).get_text()`). Without an adapter, you'd couple your code directly to the external system's API.

---

## Three Approaches (OOP → Functional Progression)

### 1. Object-Based Adapter (Composition) — Good

Wrap the external system in a new class that exposes the expected interface. The adapter **has** an instance of the adapted object (composition).

**Define the Protocol interface:**

```python
from typing import Any, Protocol

class Config(Protocol):
    def get(self, key: str, default: Any = None) -> Any | None: ...
```

**Create the adapter:**

```python
from bs4 import BeautifulSoup

class XMLAdapter:
    def __init__(self, soup: BeautifulSoup) -> None:
        self.soup = soup

    def get(self, key: str, default: Any = None) -> Any | None:
        value = self.soup.find(key)
        if value:
            return value.get_text()
        return default
```

**Usage:**

```python
adapter = XMLAdapter(bs_soup)
experiment = Experiment(adapter)  # Experiment expects Config protocol
```

The Protocol provides structural typing — `XMLAdapter` satisfies `Config` without inheriting from it. `dict` also satisfies `Config` because it already has `.get()`.

---

### 2. Class-Based Adapter (Inheritance) — Avoid

The adapter inherits from the adapted class instead of composing it:

```python
# DON'T DO THIS
class XMLAdapter(BeautifulSoup):
    def get(self, key: str, default: Any = None) -> Any | None:
        value = self.find(key)
        if value:
            return value.get_text()
        return default
```

**Why this is dangerous:** `BeautifulSoup` already has a `.get()` method with different semantics. The adapter overrides it, breaking any code that expects the original `BeautifulSoup.get()` behavior. Inheritance mixes the adapter and adaptee interfaces — composition keeps them cleanly separated.

---

### 3. Function-Based Adapter (Partial Application) — Preferred

When the adapter only needs a single method, replace the entire class with a function and use `functools.partial` to bind the external dependency.

**Define a Callable type alias:**

```python
from typing import Any, Callable

ConfigGetter = Callable[[str], Any]
```

**Write the adapter as a plain function:**

```python
from bs4 import BeautifulSoup

def get_from_bs(soup: BeautifulSoup, key: str, default: Any = None) -> Any | None:
    value = soup.find(key)
    if value:
        return value.get_text()
    return default
```

**Bind the dependency with `partial`:**

```python
from functools import partial

bs_adapter = partial(get_from_bs, soup)
experiment = Experiment(bs_adapter)  # Experiment expects ConfigGetter
```

**The client uses the Callable:**

```python
class Experiment:
    def __init__(self, config_getter: ConfigGetter) -> None:
        self.config_getter = config_getter

    def train_model(self) -> None:
        epoch_count = self.config_getter("epoch_count")
        print(f"Training for {epoch_count} epochs.")
```

This is the most Pythonic approach: minimal code, no unnecessary classes, and `partial` handles the interface mismatch. The adapter is a function, so it's easy to test, compose, and replace.

---

## JSON Works Without an Adapter

A `dict` already has `.get(key)` — no adapter needed:

```python
import json

with open("config.json") as f:
    config = json.load(f)

# Object approach: pass dict directly (satisfies Config protocol)
experiment = Experiment(config)

# Function approach: pass dict.get (satisfies ConfigGetter callable)
experiment = Experiment(config.get)
```

This is the payoff of designing against an interface: compatible systems require zero adaptation code.

---

## When to Use

- **Integrating third-party libraries** whose API doesn't match your code's expected interface
- **Switching between data sources** (JSON, XML, YAML, database) behind a common interface
- **Wrapping legacy code** that you can't modify
- **Single-method adaptation** — use the function + `partial` approach
- **Multi-method adaptation** — use the object-based approach with Protocol

## When NOT to Use

- **The interface already matches** — `dict.get()` already satisfies `Config` protocol
- **You control both sides** — modify the source directly instead of wrapping it

## Choosing the Right Approach

| Scenario | Approach |
|---|---|
| Single method to adapt | Function + `functools.partial` |
| Multiple methods to adapt | Object adapter with composition + Protocol |
| External class you cannot modify | Either approach; never use inheritance |

## Relationship to Other Patterns

- **Facade** simplifies a complex subsystem into a smaller interface. **Adapter** translates one interface to another — the complexity stays the same, just the shape changes.
- **Bridge** separates two hierarchies that vary independently. **Adapter** connects two existing, incompatible interfaces.
- **Function Wrapper** (see `patterns/functional.md`) is the simplest form of adapter — a function that calls another function with translated arguments.
