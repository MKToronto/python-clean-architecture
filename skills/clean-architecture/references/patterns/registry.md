# Registry Pattern

> Content inspired by Arjan Codes' Pythonic Patterns course.

## Problem

Creating objects from JSON or config data leads to if/elif chains that couple type strings directly to class constructors. Every new type requires modifying the creation logic.

```python
import json
from dataclasses import dataclass


@dataclass
class Pulse:
    strength: int

    def run(self) -> None:
        print(f"Sending subspace pulse with strength {self.strength}")


@dataclass
class Recalibrate:
    target: str

    def run(self) -> None:
        print(f"Recalibrating {self.target}")


@dataclass
class Reinforce:
    plating_type: str
    target: str

    def run(self) -> None:
        print(f"Reinforcing {self.target} with {self.plating_type} plating")


def main() -> None:
    with open("tasks.json") as f:
        task_data: list[dict] = json.load(f)["tasks"]

    tasks = []
    for item in task_data:
        if item["type"] == "pulse":
            tasks.append(Pulse(strength=item["strength"]))
        elif item["type"] == "recalibrate":
            tasks.append(Recalibrate(target=item["target"]))
        elif item["type"] == "reinforce":
            tasks.append(Reinforce(plating_type=item["plating_type"], target=item["target"]))

    for task in tasks:
        task.run()
```

Problems with this approach:
- The type string is directly coupled to the object constructor.
- Each task requires extracting specific arguments from the dictionary.
- Adding a new task type means adding another elif branch.
- A factory pattern does not solve this well because factories are not designed with data-driven creation in mind -- they create objects but do not handle mapping config data to constructor arguments.

---

## Classic OOP -- Class-Based Registry with Protocol Factories

Build a registry that maps type strings to factory objects. Each factory implements a Protocol with a `create` method that accepts a dictionary and returns a task.

### registry.py

```python
from typing import Any, Protocol


class Task(Protocol):
    """Represents a runnable task."""

    def run(self) -> None: ...


class TaskFactory(Protocol):
    """Creates a new task from a dictionary of arguments."""

    def create(self, args: dict[str, Any]) -> Task: ...


class TaskRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, TaskFactory] = {}

    def register(self, task_type: str, factory: TaskFactory) -> None:
        self._registry[task_type] = factory

    def unregister(self, task_type: str) -> None:
        self._registry.pop(task_type, None)

    def create(self, arguments: dict[str, Any]) -> Task:
        args_copy = arguments.copy()
        task_type = args_copy.pop("type")
        factory = self._registry[task_type]
        return factory.create(args_copy)
```

### tasks.py

```python
from typing import Any
from dataclasses import dataclass
from registry import Task


@dataclass
class Pulse:
    strength: int

    def run(self) -> None:
        print(f"Sending subspace pulse with strength {self.strength}")


class PulseFactory:
    def create(self, args: dict[str, Any]) -> Task:
        return Pulse(**args)


@dataclass
class Recalibrate:
    target: str

    def run(self) -> None:
        print(f"Recalibrating {self.target}")


class RecalibrateFactory:
    def create(self, args: dict[str, Any]) -> Task:
        return Recalibrate(**args)


@dataclass
class Reinforce:
    plating_type: str
    target: str

    def run(self) -> None:
        print(f"Reinforcing {self.target} with {self.plating_type} plating")


class ReinforceFactory:
    def create(self, args: dict[str, Any]) -> Task:
        return Reinforce(**args)
```

### main.py

```python
import json
from registry import TaskRegistry
from tasks import PulseFactory, RecalibrateFactory, ReinforceFactory


def main() -> None:
    registry = TaskRegistry()
    registry.register("pulse", PulseFactory())
    registry.register("recalibrate", RecalibrateFactory())
    registry.register("reinforce", ReinforceFactory())

    with open("tasks.json") as f:
        task_data: list[dict] = json.load(f)["tasks"]

    tasks = [registry.create(item) for item in task_data]
    for task in tasks:
        task.run()
```

This eliminates the if/elif chain but introduces boilerplate: every task type needs both a class and a factory class. Each factory does the same thing -- unpacks dictionary arguments into the constructor.

---

## Pythonic -- Dict Mapping Strings to Callables

Replace the entire class-based registry with a module-level dictionary that maps type strings to plain functions. Use `dict.pop()` to extract the type and `**kwargs` unpacking to pass the remaining data.

### registry.py

```python
from typing import Any, Callable

# Module-level registry: maps type strings to task functions
_task_functions: dict[str, Callable[..., None]] = {}


def register(task_type: str, task_fn: Callable[..., None]) -> None:
    _task_functions[task_type] = task_fn


def unregister(task_type: str) -> None:
    _task_functions.pop(task_type, None)


def run(arguments: dict[str, Any]) -> None:
    args_copy = arguments.copy()
    task_type = args_copy.pop("type")
    task_fn = _task_functions[task_type]
    task_fn(**args_copy)
```

### tasks.py

```python
def send_pulse(strength: int) -> None:
    print(f"Sending subspace pulse with strength {strength}")


def recalibrate(target: str) -> None:
    print(f"Recalibrating {target}")


def reinforce(plating_type: str, target: str) -> None:
    print(f"Reinforcing {target} with {plating_type} plating")
```

### main.py

```python
import json
from registry import register, run
from tasks import send_pulse, recalibrate, reinforce


def main() -> None:
    register("pulse", send_pulse)
    register("recalibrate", recalibrate)
    register("reinforce", reinforce)

    with open("tasks.json") as f:
        task_data: list[dict] = json.load(f)["tasks"]

    for item in task_data:
        run(item)
```

Key simplifications:
- No Protocol classes, no factory classes, no ABC.
- `pop("type")` extracts the type string and removes it from the dict in one step.
- `**args_copy` unpacks the remaining keys as keyword arguments to the function.
- Each "task" is a plain function with named parameters that match the JSON keys.

---

## Plugin System -- importlib for Self-Registering Plugins

Extend the functional registry with dynamic plugin loading. Each plugin is a standalone module that registers itself on import.

### tasks.json

```json
{
    "plugins": ["inject"],
    "tasks": [
        {"type": "pulse", "strength": 5},
        {"type": "recalibrate", "target": "sensors"},
        {"type": "inject", "material": "tachyons", "target": "deflector array"}
    ]
}
```

### inject.py (the plugin)

```python
from registry import register


def inject(material: str, target: str) -> None:
    print(f"Injecting {material} into {target}")


# Self-registration: runs when the module is imported
register("inject", inject)
```

### loader.py

```python
import importlib


def load_plugins(plugins: list[str]) -> None:
    for plugin in plugins:
        importlib.import_module(plugin)
```

### main.py

```python
import json
from registry import register, run
from tasks import send_pulse, recalibrate, reinforce
from loader import load_plugins


def main() -> None:
    register("pulse", send_pulse)
    register("recalibrate", recalibrate)
    register("reinforce", reinforce)

    with open("tasks.json") as f:
        data = json.load(f)

    # Load plugins before running tasks -- plugins register themselves on import
    load_plugins(data.get("plugins", []))

    for item in data["tasks"]:
        run(item)
```

How it works:
1. `importlib.import_module("inject")` imports the `inject.py` file.
2. Module-level code in `inject.py` calls `register("inject", inject)`.
3. The registry now knows about the "inject" type without any changes to main.
4. New plugins follow the same pattern: define a function, call `register()` at module level.

This approach enables extending the system without modifying existing code. Use cases include game level loading, data pipeline stages, and processing job definitions.

---

## When to Use / Trade-offs

**Use the registry pattern when:**
- Creating objects or dispatching behavior from serialized data (JSON, YAML, config files).
- The set of types is open-ended or expected to grow.
- You want to decouple type strings from creation logic.
- You need a plugin architecture where third parties add new types.

**Prefer the functional registry** (dict of callables) over the class-based version in most Python projects. The class-based version adds factory boilerplate for every type with no additional benefit.

**Trade-offs:**
- Registry lookup failures produce `KeyError` at runtime, not compile-time type errors. Add error handling if the data source is untrusted.
- `**kwargs` unpacking ties function parameter names to JSON key names. A mismatch produces a `TypeError` at runtime.
- The plugin system uses module-level side effects (self-registration on import). Keep plugin modules small and focused.
- For very large plugin systems, consider entry points (`importlib.metadata`) or a package discovery mechanism instead of listing plugins in config.

---

## Plugin Discovery

For systems beyond the basic plugin list in JSON, use these discovery mechanisms.

### Directory Scanning

Automatically find and load all plugin modules in a directory:

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
        module = import_module(name)
        if hasattr(module, "register"):
            module.register()
```

### `importlib.metadata` Entry Points (Modern Approach)

For distributable plugins installed as packages, use entry points — the standard mechanism used by pytest, Flask, and other frameworks:

```python
from importlib.metadata import entry_points

def load_installed_plugins() -> None:
    plugins = entry_points(group="myapp.plugins")
    for plugin in plugins:
        fn = plugin.load()  # loads the registered callable
        fn()  # call its registration function
```

Plugins declare themselves in `pyproject.toml`:

```toml
[project.entry-points."myapp.plugins"]
inject = "mypackage.inject:register"
```

### Plugin Validation via Protocol Conformance

Verify that loaded plugins satisfy the expected interface before registration:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class TaskPlugin(Protocol):
    def run(self) -> None: ...

def register_validated(task_type: str, task_class: type) -> None:
    if not issubclass(task_class, TaskPlugin):
        raise TypeError(f"{task_class.__name__} does not satisfy TaskPlugin protocol")
    _task_functions[task_type] = task_class
```

Use `@runtime_checkable` to enable `isinstance` / `issubclass` checks against the Protocol at runtime.

### Error Handling for Broken Plugins

Plugins loaded at runtime can fail. Isolate failures so one broken plugin doesn't crash the whole system:

```python
import logging

def load_plugins_safely(plugin_names: list[str]) -> None:
    for name in plugin_names:
        try:
            module = import_module(name)
            if hasattr(module, "register"):
                module.register()
        except Exception:
            logging.exception(f"Failed to load plugin: {name}")
```

For a complete plugin architecture guide (including Protocol-based interfaces, config-driven creation, and self-registering plugins), see `patterns/plugin-architecture.md`.
