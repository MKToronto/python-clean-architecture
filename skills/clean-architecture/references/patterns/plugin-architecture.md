# Plugin Architecture

**Recognize:** Adding new features requires modifying imports and core code. You need to extend the application after it's been shipped — new character types in a game, new data processors, new integrations — without touching a single line of the original codebase.

**Problem:** Hard-coded imports and if/elif chains couple the application to every feature it supports. Adding a new type means editing the factory, adding imports, and redeploying.

---

## Architecture Overview

The plugin architecture combines three patterns:

1. **Registry** (`registry.md`) — dict mapping strings to factory callables
2. **Protocol** — structural typing for plugin conformance
3. **Dynamic import** — `importlib.import_module` for runtime loading

```
Config (JSON)  →  Plugin Loader  →  Registry  →  Factory  →  Application
                      ↑
               plugins/ directory
```

---

## The Plugin Interface

Define what every plugin must provide using a Protocol or a class with `@staticmethod`:

```python
class PluginInterface:
    @staticmethod
    def initialize() -> None:
        """Entry point called by the loader to register plugin components."""
        ...
```

Uses `@staticmethod` because plugins are modules, not instances. The loader calls `initialize()` after importing the module.

---

## Config-Driven Creation

Define entities in JSON — the factory creates them dynamically:

```json
{
  "characters": [
    {"type": "sorcerer", "name": "Yennefer"},
    {"type": "wizard", "name": "Gandalf"},
    {"type": "bard", "name": "Dandelion", "instrument": "lute"}
  ],
  "plugins": ["plugins.bard"]
}
```

```python
import json
from game.factory import create
from game.loader import load_plugins

with open("level.json") as f:
    data = json.load(f)

# Load plugins BEFORE creating entities — plugins register their types
load_plugins(data.get("plugins", []))

# Single list comprehension replaces entire if/elif chain
characters = [create(item) for item in data["characters"]]
```

---

## The Factory (Registry Pattern)

```python
from typing import Any, Callable

GameCharacter = ...  # Protocol defining the expected interface

character_creation_funcs: dict[str, Callable[..., GameCharacter]] = {}

def register(character_type: str, creation_func: Callable[..., GameCharacter]) -> None:
    character_creation_funcs[character_type] = creation_func

def unregister(character_type: str) -> None:
    character_creation_funcs.pop(character_type, None)

def create(args: dict[str, Any]) -> GameCharacter:
    args_copy = args.copy()  # don't mutate the original
    character_type = args_copy.pop("type")  # extract type, pass rest as kwargs
    try:
        creation_func = character_creation_funcs[character_type]
        return creation_func(**args_copy)
    except KeyError as e:
        raise ValueError(f"Unknown character type: {character_type!r}") from e
```

**Key details:**
- `args.copy()` prevents mutation of the original config dict
- `.pop("type")` removes the metadata key so it isn't passed to the constructor
- `**args_copy` unpacks remaining keys as keyword arguments
- Exception chaining (`from e`) preserves the original error context

---

## Dynamic Plugin Loading with `importlib`

```python
from importlib import import_module

def import_module_by_name(name: str) -> PluginInterface:
    return import_module(name)  # type: ignore

def load_plugins(plugin_names: list[str]) -> None:
    for name in plugin_names:
        plugin = import_module_by_name(name)
        plugin.initialize()
```

**Why `type: ignore`:** `import_module` returns `types.ModuleType`, not `PluginInterface`. The type mismatch is confined to this one function — cleaner than alternative typing workarounds.

---

## Self-Registering Plugins

Each plugin is a standalone module that registers itself when `initialize()` is called:

```python
# plugins/bard.py
from dataclasses import dataclass
from game.factory import register

@dataclass
class Bard:
    name: str
    instrument: str = "flute"

    def make_noise(self) -> None:
        print(f"{self.name} plays {self.instrument}")

class PluginInterface:
    @staticmethod
    def initialize() -> None:
        register("bard", Bard)
```

**The plugin registers itself** — it knows how to initialize. The loader just calls the entry point. No modification to the original codebase.

---

## Protocol Conformance

Use a Protocol to define what all entities must support:

```python
from typing import Protocol

class GameCharacter(Protocol):
    name: str

    def make_noise(self) -> None: ...
```

Any class with a `name` attribute and a `make_noise()` method satisfies this Protocol — no inheritance required. The plugin's `Bard` class conforms automatically:

```python
# Built-in types
@dataclass
class Sorcerer:
    name: str
    def make_noise(self) -> None:
        print(f"{self.name} casts a spell")

# Plugin types — same Protocol, no coupling
@dataclass
class Bard:
    name: str
    instrument: str = "flute"
    def make_noise(self) -> None:
        print(f"{self.name} plays {self.instrument}")
```

---

## Directory Scanning for Auto-Discovery

For larger systems, scan a plugins directory instead of listing plugins in config:

```python
import os
from importlib import import_module
from pathlib import Path

def discover_plugins(plugin_dir: str = "plugins") -> list[str]:
    plugin_path = Path(plugin_dir)
    return [
        f"{plugin_dir}.{f.stem}"
        for f in plugin_path.glob("*.py")
        if not f.name.startswith("_")
    ]

def load_all_plugins(plugin_dir: str = "plugins") -> None:
    for name in discover_plugins(plugin_dir):
        plugin = import_module(name)
        if hasattr(plugin, "PluginInterface"):
            plugin.PluginInterface.initialize()
```

For very large systems, use `importlib.metadata` entry points — the standard mechanism for distributable plugins (used by pytest, Flask, etc.).

---

## When to Use

- **Extensible applications** — games with modding, frameworks with user extensions
- **Post-deployment features** — ship new capabilities without modifying core code
- **Multi-tenant apps** — per-tenant custom logic loaded dynamically
- **Open-source projects** — third-party developers can contribute plugins

## When NOT to Use

- **Small apps with fixed requirements** — explicit imports are simpler and more traceable
- **Performance-critical paths** — `importlib` adds overhead; use direct imports
- **Tightly coupled features** — if features depend on each other, plugins add unnecessary indirection

## Relationship to Other Patterns

- **Registry** (`registry.md`) — plugin architecture extends registry with dynamic discovery
- **Strategy** (`strategy.md`) — plugins can provide strategy functions registered at load time
- **Adapter** (`adapter.md`) — plugins may adapt external interfaces to your Protocol
- **Separate Creation from Use** (Principle 5) — the loader creates; application code uses
