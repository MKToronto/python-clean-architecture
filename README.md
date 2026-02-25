# python-clean-architecture

A Claude Code plugin that provides Clean Architecture guidance for Python/FastAPI projects.

## Attribution

The principles, patterns, and architectural approach in this plugin are inspired by and synthesized from [Arjan Codes](https://www.arjancodes.com/)' courses:

- **The Software Designer Mindset** — Seven core design principles (cohesion, coupling, abstractions, composition, creation/use separation, data-first design, simplicity)
- **Pythonic Patterns** — Classic GoF patterns reimagined for Python using Protocol, Callable, functools.partial, and closures
- **Complete Extension** — Three-layer FastAPI architecture (Routers → Operations → Database) with Protocol-based dependency injection

This plugin distills those principles into actionable guidance for Claude Code. It is not a reproduction of course content. If you find this useful, consider supporting Arjan's work at [arjancodes.com](https://www.arjancodes.com/).

## Installation

1. Add the marketplace:
```
/plugin marketplace add MKToronto/python-clean-architecture
```

2. Install the plugin:
```
/plugin install python-clean-architecture@python-clean-architecture
```

3. Restart Claude Code (`/exit` then `claude`) to load the plugin.

Or download the repo and test locally without installing:

```bash
git clone https://github.com/MKToronto/python-clean-architecture.git
claude --plugin-dir /path/to/python-clean-architecture
```

## Updating

```
/plugin marketplace update python-clean-architecture
```

Then restart Claude Code (`/exit` then `claude`).

## Usage

### Automatic (Skill)

The skill triggers automatically when you ask Claude Code to:

- "Scaffold a new FastAPI project"
- "Set up clean architecture"
- "Refactor to clean architecture"
- "Add a new endpoint / router / use case / repository"
- "Review my code structure"
- "Apply design patterns in Python"
- "Decouple my code"
- "Make my code testable"

Or mention: layered architecture, dependency injection, Protocol-based design, Pythonic design patterns.

### Slash Commands

```
/review-architecture              Review current directory
/review-architecture src/         Review a specific directory
/review-architecture app/main.py  Review a specific file
```

The review checks:
- **Architecture layers** — Three-layer separation, no layer skipping, router as composition root
- **7 design principles** — Cohesion, coupling, abstractions, composition, creation/use, data-first, simplicity
- **17 code quality rules** — Naming, nesting, types, error handling, imports, structure
- **Pythonic patterns** — Strategy as Callable, Factory as dict mapping, Protocol over ABC

Findings are reported by severity (Critical / Important / Suggestions) with file/line references and fix snippets.

### All Commands

**Review & Analysis:**
```
/review-architecture [path]       Full architecture review (standard or in-depth)
/check-quality [path]             Quick check against 17 code quality rules
/suggest-patterns [path]          Recommend Pythonic design patterns for your code
/decouple [path]                  Find tight coupling and suggest DI improvements
```

**Refactoring:**
```
/make-pythonic [path]             Refactor to Pythonic patterns (ABC→Protocol, if/elif→dict, etc.)
/extract-god-class [path]         Find and split god classes into focused collaborators
```

**Scaffolding:**
```
/scaffold-api <project-name>      Generate a new FastAPI project with clean architecture
/add-endpoint <entity-name>       Scaffold a new endpoint across all three layers
```

`/scaffold-api` generates a full project structure with Pydantic models, operations, routers, database layer, and tests. `/add-endpoint` adds a new entity to an existing project — it creates files across all three layers (router + operations + DB model + Pydantic models + tests) and wires them into `main.py`.

## What's Inside

```
python-clean-architecture/
├── .claude-plugin/
│   ├── plugin.json                         Plugin manifest
│   └── marketplace.json                    Marketplace catalog
├── README.md                               This file
├── LICENSE                                 MIT license
├── commands/
│   ├── review-architecture.md              Full architecture review
│   ├── check-quality.md                    Quick 17-rule quality check
│   ├── suggest-patterns.md                 Recommend Pythonic patterns
│   ├── decouple.md                         Find coupling, suggest DI
│   ├── make-pythonic.md                    Refactor to Pythonic patterns
│   ├── extract-god-class.md                Split god classes
│   ├── scaffold-api.md                     Generate FastAPI project
│   └── add-endpoint.md                     Scaffold endpoint across layers
└── skills/
    └── clean-architecture/
        ├── SKILL.md                        Core skill (loaded when triggered)
        ├── references/
        │   ├── design-principles.md        7 principles with refactoring recipes
        │   ├── layered-architecture.md     3-layer FastAPI guide with full code
        │   ├── testable-api.md             Stub-based testing strategy
        │   ├── testing-advanced.md         Pytest, property-based, stateful testing
        │   ├── rest-api-design.md          HTTP methods, status codes, OpenAPI
        │   ├── code-quality.md             17 rules + code review checklist
        │   ├── classes-and-dataclasses.md  Classes vs dataclasses decision guide
        │   ├── function-design.md          Pure functions, closures, partial, HOFs
        │   ├── data-structures.md          Choosing the right data structure
        │   ├── error-handling.md           Custom exceptions, context managers
        │   ├── monadic-error-handling.md   Railway-oriented Result types
        │   ├── types-and-type-hints.md     Python's type system, Callable types
        │   ├── project-organization.md     Modules, packages, folder structure
        │   ├── context-managers.md         __enter__/__exit__, @contextmanager
        │   ├── decorators.md               Retry, logging, timing, parameterized
        │   ├── async-patterns.md           Async/await, gather, TaskGroup
        │   ├── pydantic-validation.md      Pydantic v2 validators, ConfigDict
        │   ├── pattern-matching.md         match/case structural patterns
        │   ├── pythonic-patterns.md        Quick reference for all 23 patterns
        │   └── patterns/
        │       ├── strategy.md             Full OOP → functional progression
        │       ├── abstract-factory.md     Tuples of functions + partial
        │       ├── bridge.md               Bound methods, when to stop
        │       ├── command.md              Undo closures, batch commands
        │       ├── notification.md         Observer → Mediator → Pub/Sub
        │       ├── registry.md             Dict mapping, importlib plugins
        │       ├── template-method.md      Free function + Protocol
        │       ├── pipeline.md             Chain of Responsibility, compose
        │       ├── functional.md           Callback, Wrapper, Builder
        │       ├── value-objects.md        Validated domain primitives
        │       ├── event-sourcing.md       Immutable events, projections
        │       ├── cqrs.md                 Separate read/write models
        │       ├── builder.md              Fluent API, frozen product
        │       ├── unit-of-work.md         Transaction context managers
        │       ├── singleton.md            Module-level instance, metaclass
        │       ├── state.md                Protocol-based state objects
        │       ├── adapter.md              Composition + partial adaptation
        │       ├── facade.md               Simplified subsystem interface
        │       ├── retry.md                Exponential backoff decorator
        │       ├── lazy-loading.md         cache, cached_property, generators
        │       └── plugin-architecture.md  Config-driven, importlib discovery
        └── examples/
            └── fastapi-hotel-api/          Complete working FastAPI project
                ├── main.py
                ├── models/             Pydantic models + DataInterface Protocol
                ├── operations/         Business logic (accepts Protocol)
                ├── routers/            API endpoints (composition root)
                └── db/                 SQLAlchemy + generic DBInterface

```

## Key Concepts

### Three-Layer Architecture

```
Routers (API)  →  Operations (business logic)  →  Database (persistence)
```

Each layer depends only on the layer below. The router is the composition root where concrete DB implementations are injected into operations via the `DataInterface` Protocol.

### Seven Design Principles

1. High Cohesion — Single responsibility per unit
2. Low Coupling — Minimize dependencies, Law of Demeter
3. Depend on Abstractions — Protocol + Callable for DI
4. Composition over Inheritance — Never mixins, shallow hierarchies only
5. Separate Creation from Use — Dict mapping, creator functions, one composition root
6. Start with the Data — Information Expert, fix data structures first
7. Keep Things Simple — DRY, KISS, YAGNI (but avoid hasty abstractions)

### Pythonic Pattern Defaults

- Protocol over ABC (unless shared superclass state needed)
- `functools.partial` over wrapper classes
- Closures over factory class hierarchies
- `Callable` type aliases over single-method abstract classes
- Dict mapping over if/elif chains
- Readability over dogmatic functional purity

23 design patterns implemented the Pythonic way:

**Core Patterns:**
- **Strategy** — `Callable` type alias, pass functions as args
- **Abstract Factory** — Tuples of functions + `functools.partial`
- **Bridge** — `Callable` type alias replaces abstract reference
- **Command** — Functions returning undo closures
- **Pub/Sub** — Dict-based `subscribe(event, handler)` / `post_event(event, data)`
- **Registry** — `dict[str, Callable]` mapping + `**kwargs` unpacking
- **Template Method** — Free function + Protocol parameter
- **Pipeline** — `functools.reduce` for composition
- **Callback / Wrapper / Builder** — Functional patterns for event handling, interface translation, and configuration

**Extended Patterns:**
- **Value Objects** — Subclass built-in types with `__new__` validation, or frozen dataclass
- **Event Sourcing** — Immutable events, append-only EventStore, projection functions
- **CQRS** — Separate write model + read projection, projector function after writes
- **Builder** — Fluent API with `Self` return type, `.build()` returns frozen product
- **Unit of Work** — Context manager wrapping transaction: commit on success, rollback on error
- **Singleton** — Module-level instance (preferred), or metaclass with `_instances` dict
- **State** — Protocol-based state objects, context delegates to current state
- **Adapter** — Protocol interface + `functools.partial` for single-method adaptation
- **Facade** — Simplified interface class, `functools.partial` to bind dependencies
- **Retry** — `@retry` decorator with exponential backoff, fallback strategies
- **Lazy Loading** — `functools.cache`, `cached_property`, generators, `__getattr__`
- **Plugin Architecture** — Config-driven creation, `importlib` auto-discovery, self-registering modules
