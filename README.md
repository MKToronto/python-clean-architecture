# python-clean-architecture — Claude Code Plugin

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) plugin that provides Clean Architecture guidance for Python/FastAPI projects. Scaffold, review, and refactor Python projects with design principles and Pythonic patterns — directly inside Claude Code.

## Attribution

The principles, patterns, and architectural approach in this plugin are inspired by and synthesized from [Arjan Codes](https://www.arjancodes.com/)' courses:

- **The Software Designer Mindset** — Seven core design principles (cohesion, coupling, abstractions, composition, creation/use separation, data-first design, simplicity)
- **Pythonic Patterns** — Classic GoF patterns reimagined for Python using Protocol, Callable, functools.partial, and closures
- **Complete Extension** — Three-layer FastAPI architecture (Routers → Operations → Database) with Protocol-based dependency injection

The specific Pythonic framing (Protocol-based DI, functional pattern progression, three-layer FastAPI architecture) originates from his teaching. This plugin distills those principles into actionable guidance for Claude Code — it is not a reproduction of course content. If you find this useful, consider supporting Arjan's work at [arjancodes.com](https://www.arjancodes.com/), [github.com/arjancodes](https://github.com/arjancodes), and [youtube.com/arjancodes](https://www.youtube.com/arjancodes).

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
- **22 code quality rules** — Naming, nesting, types, error handling, imports, structure
- **Pythonic patterns** — All 25 patterns checked (Strategy as Callable, Factory as dict mapping, Protocol over ABC, etc.)

Findings are reported by severity (Critical / Important / Suggestions) with file/line references and fix snippets.

**Example output** (fictional `bookstore-api/`). See the [color-coded version](https://mktoronto.github.io/python-clean-architecture/) on the landing page.

```text
$ /review-architecture bookstore-api/

Architecture Summary
----------------------

Layers
------
API:        routers/books.py, routers/orders.py
Logic:      services/book_service.py, services/order_service.py
Database:   db/models.py, db/database.py
Unclear:    utils/helpers.py (mixed concerns)

Dependency Flows
----------------
routers/books.py -> book_service.py -> db/database.py        [ok]
routers/orders.py -> db/models.py                             [!] layer skip
routers/orders.py -> order_service.py -> db/database.py       [ok]

What Works Well
----------------
[ok] Clean separation in routers/books.py -- never touches DB
[ok] Good Pydantic model separation: BookCreate / Book
[ok] book_service.py accepts data_interface -- proper DI

Findings by Severity
----------------------

Critical

1. Layer skip -- router imports DB directly
   routers/orders.py:3
   Principle: P3 Depend on Abstractions
   Fix: Move DB access into services, pass DataInterface.

   # Before
   from db.models import OrderModel

   @router.post("/orders")
   def create_order(data: OrderCreate):
       order = OrderModel(**data.dict())

   # After
   @router.post("/orders", status_code=201)
   def create_order(data: OrderCreate):
       return create_order_op(data, data_interface=db_interface)

Important

2. God class -- OrderService has 6 responsibilities
   services/order_service.py:1 -- 280 lines
   Principle: P1 High Cohesion
   Fix: Extract PaymentService, InventoryService, NotificationService.

3. Missing type hints
   utils/helpers.py:12 -- def format_price(amount, currency):
   Fix: def format_price(amount: Decimal, currency: str) -> str:

Suggestions

4. if/elif chain for discount logic
   services/order_service.py:145
   Pattern: Strategy -- Callable type alias

   # Before
   if discount_type == "percentage": ...
   elif discount_type == "fixed": ...

   # After
   DiscountStrategy = Callable[[Decimal, int], Decimal]
   DISCOUNTS: dict[str, DiscountStrategy] = {
       "percentage": apply_percentage,
       "fixed": apply_fixed,
       "bogo": apply_bogo,
   }
   final_price = DISCOUNTS[discount_type](price, quantity)

5. Bare string constants for order status
   services/order_service.py:22
   Fix: Use StrEnum

   class OrderStatus(StrEnum):
       PENDING = "pending"
       SHIPPED = "shipped"
       DELIVERED = "delivered"
```

### All Commands

**Review & Analysis:**
```
/review-architecture [path]       Full architecture review (standard or in-depth)
/review-api-design [path]         Review REST API endpoints for HTTP conventions
/check-quality [path]             Quick check against 22 code quality rules
/suggest-patterns [path]          Recommend Pythonic design patterns for your code
/decouple [path]                  Find tight coupling and suggest DI improvements
```

**Refactoring:**
```
/make-pythonic [path]             Refactor to Pythonic patterns (ABC→Protocol, if/elif→dict, etc.)
/extract-god-class [path]         Find and split god classes into focused collaborators
```

**Scaffolding & Testing:**
```
/scaffold-api <project-name>      Generate a new FastAPI project with clean architecture
/add-endpoint <entity-name>       Scaffold a new endpoint across all three layers
/scaffold-tests [path]            Generate stub-based tests for existing operations
```

`/scaffold-api` generates a full project structure with Pydantic models, operations, routers, database layer, and tests. `/add-endpoint` adds a new entity to an existing project — it creates files across all three layers (router + operations + DB model + Pydantic models + tests) and wires them into `main.py`. `/scaffold-tests` generates DataInterfaceStub-based tests for existing operations without requiring a database.

## What's Inside

```text
python-clean-architecture/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── README.md
├── LICENSE
├── commands/
│   ├── review-architecture.md
│   ├── review-api-design.md
│   ├── check-quality.md
│   ├── suggest-patterns.md
│   ├── decouple.md
│   ├── make-pythonic.md
│   ├── extract-god-class.md
│   ├── scaffold-api.md
│   ├── scaffold-tests.md
│   └── add-endpoint.md
└── skills/clean-architecture/
    ├── SKILL.md
    ├── references/
    │   ├── design-principles.md
    │   ├── layered-architecture.md
    │   ├── testable-api.md
    │   ├── testing-advanced.md
    │   ├── rest-api-design.md
    │   ├── code-quality.md
    │   ├── classes-and-dataclasses.md
    │   ├── function-design.md
    │   ├── data-structures.md
    │   ├── error-handling.md
    │   ├── monadic-error-handling.md
    │   ├── types-and-type-hints.md
    │   ├── project-organization.md
    │   ├── context-managers.md
    │   ├── decorators.md
    │   ├── async-patterns.md
    │   ├── pydantic-validation.md
    │   ├── pattern-matching.md
    │   ├── grasp-principles.md
    │   ├── domain-driven-design.md
    │   ├── pythonic-patterns.md
    │   └── patterns/          (25 pattern files)
    │       ├── strategy.md
    │       ├── registry.md
    │       ├── command.md
    │       ├── builder.md
    │       ├── repository.md
    │       ├── cqrs.md
    │       └── ...
    └── examples/
        └── fastapi-hotel-api/
            ├── main.py
            ├── models/
            ├── operations/
            ├── routers/
            └── db/
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

25 design patterns implemented the Pythonic way:

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
- **Repository** — Protocol interface for CRUD, concrete implementations per storage backend
- **Fluent Interface** — Methods return `self` for chaining, domain-specific verbs for readability
- **Plugin Architecture** — Config-driven creation, `importlib` auto-discovery, self-registering modules

## Also available for

- **Codex CLI** — [python-clean-architecture-codex](https://github.com/MKToronto/python-clean-architecture-codex) (agent skill for Codex)
