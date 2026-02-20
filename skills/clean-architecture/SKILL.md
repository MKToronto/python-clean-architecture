---
name: Python Clean Architecture
description: This skill should be used when the user asks to "scaffold a FastAPI project", "set up clean architecture", "refactor to clean architecture", "add a new endpoint", "add a router", "add a use case", "add a repository", "review my code structure", "apply design patterns in Python", "decouple my code", "improve code quality", "make my code testable", or mentions layered architecture, dependency injection, Protocol-based design, or Pythonic design patterns for Python/FastAPI projects.
version: 0.4.0
---

# Python Clean Architecture

Provide Clean Architecture guidance for Python projects, specifically FastAPI APIs. Based on seven core design principles, Pythonic implementations of classic patterns, and a three-layer architecture (Routers → Operations → Database).

> **Attribution:** The principles, patterns, and architectural approach in this skill are inspired by and synthesized from [Arjan Codes](https://www.arjancodes.com/)' courses: *The Software Designer Mindset*, *Pythonic Patterns*, and *Complete Extension*. The specific Pythonic framing (Protocol-based DI, functional pattern progression, three-layer FastAPI architecture) originates from his teaching. This plugin distills those principles into actionable guidance for Claude Code — it is not a reproduction of course content.

## When to Apply

- Scaffolding new FastAPI projects with clean separation of concerns
- Refactoring existing Python code to reduce coupling and increase cohesion
- Adding new components (endpoints, use cases, repositories, models)
- Reviewing code for design quality and Pythonic idiom adherence
- Making code testable through dependency injection and Protocol-based abstractions

## Core Architecture: Three Layers

Every FastAPI project follows a strict three-layer dependency flow:

```
Routers (API layer)  →  Operations (business logic)  →  Database (persistence)
```

Each layer depends ONLY on the layer below it. Never skip layers.

### Layer Responsibilities

**Routers** — HTTP interface. Accept requests, call operations, return responses. No business logic. Act as the composition root where concrete implementations are injected.

**Operations** — Business logic. Accept a `DataInterface` (Protocol) parameter for data access. Compute derived values, enforce rules, orchestrate workflows. Never import database modules directly.

**Database** — Persistence. Implement the `DataInterface` Protocol using SQLAlchemy, file storage, or any backend. Expose `read_by_id`, `read_all`, `create`, `update`, `delete` methods. Return `DataObject = dict[str, Any]` to decouple from ORM models.

### The DataInterface Protocol

```python
from typing import Any, Protocol

DataObject = dict[str, Any]

class DataInterface(Protocol):
    def read_by_id(self, id: str) -> DataObject: ...
    def read_all(self) -> list[DataObject]: ...
    def create(self, data: DataObject) -> DataObject: ...
    def update(self, id: str, data: DataObject) -> DataObject: ...
    def delete(self, id: str) -> None: ...
```

Operations accept `data_interface: DataInterface` as a parameter. The router passes the concrete implementation. This is dependency injection — no ABC inheritance needed.

### Pydantic Models

Define separate Create and Read models per entity:

```python
class CustomerCreate(BaseModel):
    name: str
    email: str

class Customer(BaseModel):
    id: str
    name: str
    email: str
```

Use `**data.dict()` to unpack Pydantic models into DataObject dicts. Use `exclude_none=True` on update models for partial updates.

## Seven Design Principles

When writing or reviewing code, apply these principles in order of priority:

1. **High Cohesion** — Each class/function has a single responsibility. Extract class when a class does two things. Extract function when a function does two things.
2. **Low Coupling** — Minimize dependencies. Move methods to the class that owns the data (Information Expert). Pass only what a function needs.
3. **Depend on Abstractions** — Use `Protocol` for structural typing and `Callable` type aliases for function injection. Patterns emerge from good abstraction.
4. **Composition over Inheritance** — Extract shared behavior into standalone classes with a Protocol interface. Use `list[PaymentSource]` patterns. Never use mixins.
5. **Separate Creation from Use** — One composition root (the router or main function). Dictionary mapping over if/elif chains. Creator functions for complex construction.
6. **Start with the Data** — Fix data structures first; methods and layers follow. Extract domain classes from prefixed fields. Eliminate parallel lists.
7. **Keep Things Simple** — DRY (but avoid hasty abstractions). KISS (simplest design that works). YAGNI (implement only what is needed now).

## Pythonic Pattern Selection

When encountering these code smells, apply the corresponding pattern:

| Code Smell | Pattern | Pythonic Implementation |
|---|---|---|
| Long if/elif switching behavior | Strategy | `Callable` type alias, pass functions as args |
| Need to create objects from config/JSON | Registry | `dict[str, Callable]` mapping + `**kwargs` unpacking |
| Event/notification side effects mixed with core logic | Pub/Sub | `subscribe(event, handler)` / `post_event(event, data)` dict-based |
| Duplicated algorithm across classes | Template Method | Extract to free function + Protocol parameter |
| Two independent hierarchies that vary | Bridge | `Callable` type alias replaces abstract reference |
| Need undo/batch/queue operations | Command | Functions returning undo closures |
| Object creation coupled to usage | Abstract Factory | Tuples of functions + `functools.partial` |
| Sequential data transformations | Pipeline | `functools.reduce` for composition, or framework `.pipe()` |
| Need to react to events without coupling | Callback | Function passed as argument, called when event occurs |
| Reusing a function with a different interface | Function Wrapper | Calls another function, translates its arguments |
| Separating configuration from usage | Function Builder | Higher-order function returns a configured function |

### Default preferences for all patterns:

- **Protocol over ABC** — unless shared state in the superclass is needed
- **`functools.partial`** — to configure generic functions rather than creating wrapper classes
- **Closures** — to separate configuration-time args from runtime args
- **Don't go full functional** — find the happy medium; readability is the ultimate arbiter

## Scaffolding a New Project

When asked to create a new FastAPI project, generate this structure:

```
project_name/
├── src/
│   ├── main.py              # FastAPI app, include_router, startup events
│   ├── routers/
│   │   ├── __init__.py
│   │   └── {entity}.py      # APIRouter, endpoint functions
│   ├── operations/
│   │   ├── __init__.py
│   │   └── {entity}.py      # Business logic functions
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py       # Engine, SessionLocal, Base
│   │   ├── db_interface.py   # Generic DBInterface class
│   │   └── models.py         # SQLAlchemy models
│   └── models/
│       ├── __init__.py
│       └── {entity}.py       # Pydantic models + DataInterface Protocol
├── tests/
│   └── test_{entity}.py      # Tests using DataInterfaceStub
├── requirements.txt
└── .gitignore
```

## Testing Strategy

Create a `DataInterfaceStub` base class that stores data in a plain dict. Override specific methods in test-specific subclasses. Pass the stub to operations functions — no database needed.

```python
class DataInterfaceStub:
    def __init__(self):
        self.data: dict[str, DataObject] = {}
    def read_by_id(self, id: str) -> DataObject:
        return self.data[id]
    def read_all(self) -> list[DataObject]:
        return list(self.data.values())
    def create(self, data: DataObject) -> DataObject:
        self.data[data["id"]] = data
        return data
    def update(self, id: str, data: DataObject) -> DataObject:
        self.data[id].update(data)
        return self.data[id]
    def delete(self, id: str) -> None:
        del self.data[id]
```

## Additional Resources

### Reference Files

For detailed guidance beyond this overview, consult:

**Architecture & Design:**
- **`references/design-principles.md`** — Full treatment of the seven design principles with refactoring recipes and code examples
- **`references/layered-architecture.md`** — Detailed three-layer architecture guide: DataInterface, DBInterface, router composition, Pydantic models, to_dict utility
- **`references/testable-api.md`** — Testing strategy: stub-based testing, DataInterfaceStub, test isolation, no-database testing

**Python Fundamentals:**
- **`references/classes-and-dataclasses.md`** — When to use classes vs dataclasses, @dataclass, field(), frozen, encapsulation
- **`references/function-design.md`** — Pure functions, higher-order functions, closures, functools.partial, classes vs functions vs modules
- **`references/data-structures.md`** — Choosing list vs dict vs tuple vs set, enums, performance trade-offs
- **`references/types-and-type-hints.md`** — Python's type system, Callable types, nominal vs structural typing, best practices
- **`references/error-handling.md`** — Custom exceptions, context managers, error handling layers, anti-patterns
- **`references/code-quality.md`** — 17 code quality rules: naming, nesting, flags, type abuse, and code review checklist
- **`references/project-organization.md`** — Modules, packages, imports, folder structure, avoid "utils" anti-pattern

**Pythonic Patterns:**
- **`references/pythonic-patterns.md`** — Quick reference lookup table for all 10 patterns (use for reviews and pattern selection)

**Pythonic Patterns (full progressions from OOP → functional):**
- **`references/patterns/strategy.md`** — Callable type alias, closures, functools.partial
- **`references/patterns/abstract-factory.md`** — Tuples of functions, partial, builder functions
- **`references/patterns/bridge.md`** — Bound methods as callables, when to stop going functional
- **`references/patterns/command.md`** — Functions returning undo closures, batch via list comprehension
- **`references/patterns/notification.md`** — Observer, Mediator, and Pub/Sub with dict-based subscribe/post_event
- **`references/patterns/registry.md`** — Dict mapping + **kwargs unpacking, self-registering plugins via importlib
- **`references/patterns/template-method.md`** — Free function + Protocol parameters, protocol segregation
- **`references/patterns/pipeline.md`** — Chain of Responsibility, functools.reduce composition, pandas .pipe()
- **`references/patterns/functional.md`** — Callback, Function Wrapper, Function Builder patterns

### Example Files

- **`examples/fastapi-hotel-api/`** — Complete working FastAPI project demonstrating all patterns: rooms, customers, bookings with computed prices
