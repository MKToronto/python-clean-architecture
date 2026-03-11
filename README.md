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

**Example output** (from reviewing a test `bookstore-api/` project). See the [color-coded version](https://mktoronto.github.io/python-clean-architecture/) on the landing page.

```text
$ /review-architecture bookstore-api/

Architecture Summary
----------------------

Layers
------
API:        routers/books.py, routers/orders.py
Logic:      services/book_service.py, services/order_service.py
Database:   db/database.py (models + session factory)
Models:     models/book.py, models/order.py (Pydantic)
Unclear:    utils/helpers.py (formatting + DB queries -- mixed concerns)

Dependency Flows
----------------
routers/books.py -> services/book_service.py -> db/database.py       [ok] (no abstraction)
routers/orders.py -> services/order_service.py -> db/database.py     [ok] (no abstraction)
routers/orders.py -> db/database.py                                   [!] layer skip
utils/helpers.py -> db/database.py                                    [!] mixed concerns

Layer Violations
----------------
[!] routers/orders.py:2 imports SessionLocal + OrderModel directly
[!] routers/orders.py:21 performs raw DB query inside an endpoint
[!] utils/helpers.py:1 imports DB layer -- utility module should not touch persistence
[!] No DataInterface Protocol exists -- all services hardcode SessionLocal()

What Works Well
----------------
[ok] Good Pydantic model separation -- BookCreate / Book and OrderCreate / Order
     properly separate input from output (models/book.py, models/order.py)
[ok] Clean main.py -- simple composition with tagged routers, no business logic
[ok] Consistent router structure -- proper APIRouter() with prefix/tag organization
[ok] Book service functions are individually small -- each under 10 lines

Findings by Severity
----------------------

Critical

1. Layer skip -- router queries DB directly
   routers/orders.py:2,19-32
   Principles: P3 Depend on Abstractions, P2 Low Coupling

   The read_order endpoint imports SessionLocal and OrderModel, then runs
   raw SQLAlchemy queries inside the router. Bypasses the service layer.

   # Before (routers/orders.py:19-32)
   from db.database import SessionLocal, OrderModel

   @router.get("/{order_id}")
   def read_order(order_id: int):
       db = SessionLocal()
       order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
       db.close()
       ...

   # After -- delegate to service, raise proper HTTP errors
   from fastapi import HTTPException

   @router.get("/{order_id}", response_model=Order)
   def read_order(order_id: int):
       order = order_service.get_order(order_id)
       if not order:
           raise HTTPException(status_code=404, detail="Order not found")
       return order

2. No dependency injection -- all services hardcode DB access
   services/book_service.py:1, services/order_service.py:3
   Principle: P3 Depend on Abstractions

   Every function creates SessionLocal() internally. No DataInterface
   Protocol exists. Testing requires a real database.

   # Before (services/book_service.py:1,5-6)
   from db.database import SessionLocal, BookModel

   def create_book(data: BookCreate) -> Book:
       db = SessionLocal()
       book = BookModel(**data.dict())
       ...

   # After -- define a Protocol, inject it
   class BookDataInterface(Protocol):
       def create(self, data: dict) -> dict: ...
       def get_all(self) -> list[dict]: ...
       def get_by_id(self, book_id: int) -> dict | None: ...

   def create_book(data: BookCreate, data_interface: BookDataInterface) -> Book:
       result = data_interface.create(data.model_dump())
       return Book(**result)

3. No resource management -- leaked DB connections on exceptions
   services/book_service.py:6-11, services/order_service.py (every method)
   Principle: P7 Keep Things Simple | Rule: #13 Use Context Managers

   Every function does db = SessionLocal() ... db.close(). If any line
   between them raises, the connection leaks. OrderService methods have
   multiple early return paths each needing their own db.close().

   # Before (services/order_service.py:10-14)
   db = SessionLocal()
   book = db.query(BookModel).filter(BookModel.id == book_id).first()
   if not book:
       db.close()
       return None

   # After -- context manager guarantees cleanup
   @contextmanager
   def get_session():
       session = SessionLocal()
       try:
           yield session
       finally:
           session.close()

   def get_order(self, order_id: int) -> Order | None:
       with get_session() as db:
           order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
           return Order(**order.__dict__) if order else None

Important

4. God class -- OrderService has 7 responsibilities
   services/order_service.py:6 -- 177 lines
   Principle: P1 High Cohesion

   Handles: order CRUD, discount calculation, email notifications,
   inventory management, logging, refund processing, and shipping
   calculation. The docstring says it: "Handles orders, payments,
   inventory, notifications, discounts, and shipping."

   Fix: Extract into focused collaborators --
   DiscountCalculator, NotificationService, ShippingCalculator,
   RefundProcessor. Keep OrderOperations for pure CRUD only.

5. Broad exception catching -- except Exception: pass
   services/order_service.py:163-164
   Rule: #12 No Broad Exception Catching

   _send_email catches Exception and silently discards it. A typo inside
   the method, a TypeError, even a KeyboardInterrupt would be swallowed.
   Order appears to succeed but email silently fails with no trace.

   # Before
   def _send_email(self, to, subject, body):
       try:
           ...
       except Exception:
           pass

   # After -- catch specific errors, log failures
   def _send_email(self, to: str, subject: str, body: str) -> None:
       try:
           ...
       except (smtplib.SMTPException, ConnectionError) as e:
           logger.warning("Failed to send email to %s: %s", to, e)

6. Missing type hints on 15+ functions
   Multiple files
   Rule: Type hints on all function parameters and return types

   File                            Function                         Missing
   ------------------------------  -------------------------------  ---------------------
   services/book_service.py:15     get_all_books()                  return type
   services/book_service.py:25     get_book(book_id)                param + return
   services/book_service.py:34     search_books(query)              param + return
   services/order_service.py:9     create_order(self, ...)          all params + return
   services/order_service.py:66    get_order(self, order_id)        param + return
   services/order_service.py:80    update_status(self, ...)         all params + return
   services/order_service.py:105   cancel_order(self, order_id)     param + return
   services/order_service.py:133   get_order_history(self, ...)     param + return
   services/order_service.py:139   calculate_shipping(self, ...)    param + return
   services/order_service.py:154   _send_email(self, ...)           all params + return
   utils/helpers.py:4              format_price(amount, currency)   all params + return
   utils/helpers.py:15             get_bestsellers(limit)           param + return
   utils/helpers.py:22             validate_isbn(isbn)              param + return
   utils/helpers.py:30             generate_report()                return

7. Error responses return 200 with error body instead of HTTPException
   routers/books.py:21-22, routers/orders.py:13-14,24-25

   Returning {"error": "Book not found"} sends HTTP 200 with an error
   body. Clients cannot distinguish success from failure by status code.

   # Before (routers/books.py:20-23) -- returns HTTP 200 with error!
   book = get_book(book_id)
   if not book:
       return {"error": "Book not found"}
   return book

   # After -- proper HTTP semantics
   from fastapi import HTTPException

   book = get_book(book_id)
   if not book:
       raise HTTPException(status_code=404, detail="Book not found")
   return book

8. Missing HTTP status codes on POST endpoints
   routers/books.py:8, routers/orders.py:10

   POST endpoints default to 200 instead of 201 Created.

   # Before
   @router.post("/")
   def add_book(data: BookCreate):

   # After
   @router.post("/", status_code=201, response_model=Book)
   def add_book(data: BookCreate):

9. Returning raw dicts instead of Pydantic models
   services/book_service.py:20-22, services/order_service.py:58-64,71-77
   Principle: P6 Start with the Data

   Functions return hand-built {"id": ..., "title": ...} dicts instead
   of using the Pydantic models already defined in models/. Loses type
   safety, validation, serialization control, and IDE support.

   # Before (services/book_service.py:19-22)
   result = []
   for b in books:
       result.append({"id": b.id, "title": b.title, "author": b.author,
                      "isbn": b.isbn, "price": b.price})
   return result

   # After -- use the model you already defined
   return [Book(id=b.id, title=b.title, author=b.author,
                isbn=b.isbn, price=b.price) for b in books]

10. Deprecated Pydantic v1 API
    services/book_service.py:7 -- data.dict()

    Pydantic v2 renamed .dict() to .model_dump(). The old method
    still works but is deprecated and will be removed.

    # Before (Pydantic v1)
    book = BookModel(**data.dict())

    # After (Pydantic v2)
    book = BookModel(**data.model_dump())

Suggestions

11. if/elif chain for discount logic -- Strategy pattern
    services/order_service.py:19-31
    Pattern: Strategy -- Callable type alias + dict mapping

    # Before (services/order_service.py:19-31)
    if quantity >= 10:
        discount_type = "bulk"
    elif quantity >= 5:
        discount_type = "medium"
    else:
        discount_type = "none"

    if discount_type == "bulk":
        total = total * 0.8
    elif discount_type == "medium":
        total = total * 0.9
    elif discount_type == "none":
        pass

    # After -- discount strategies as functions
    from typing import Callable

    DiscountFn = Callable[[float, int], float]

    def bulk_discount(total: float, quantity: int) -> float:
        return total * 0.8

    def medium_discount(total: float, quantity: int) -> float:
        return total * 0.9

    def no_discount(total: float, quantity: int) -> float:
        return total

    def get_discount(quantity: int) -> DiscountFn:
        if quantity >= 10:
            return bulk_discount
        elif quantity >= 5:
            return medium_discount
        return no_discount

    # Usage
    discount = get_discount(quantity)
    total = discount(total, quantity)

12. if/elif chain for currency formatting -- dict mapping
    utils/helpers.py:4-12
    Pattern: Registry -- dict mapping replaces if/elif

    # Before
    def format_price(amount, currency):
        if currency == "USD":
            return f"${amount:.2f}"
        elif currency == "EUR":
            return f"E{amount:.2f}"
        elif currency == "GBP":
            return f"L{amount:.2f}"
        else:
            return f"{amount:.2f} {currency}"

    # After
    CURRENCY_SYMBOLS: dict[str, str] = {
        "USD": "$", "EUR": "E", "GBP": "L",
    }

    def format_price(amount: float, currency: str) -> str:
        symbol = CURRENCY_SYMBOLS.get(currency)
        if symbol:
            return f"{symbol}{amount:.2f}"
        return f"{amount:.2f} {currency}"

13. Bare string constants for order status -- use StrEnum
    services/order_service.py:38,86,89,95,111,114

    # Before -- typo-prone strings scattered across the codebase
    status="pending"
    if order.status != "pending":
    if new_status == "shipped":

    # After
    class OrderStatus(StrEnum):
        PENDING = "pending"
        SHIPPED = "shipped"
        DELIVERED = "delivered"
        CANCELLED = "cancelled"

14. Mixed concerns in utils/helpers.py -- split by domain
    utils/helpers.py:1-38
    Principle: P1 High Cohesion | Rule: #16 Avoid Generic Package Names

    Contains formatting (format_price), validation (validate_isbn),
    DB queries (get_bestsellers), and reporting (generate_report).
    Four unrelated responsibilities. The utils/ name is a dumping ground.

    Fix: Move get_bestsellers/generate_report into services/.
    Move format_price into formatting.py. Move validate_isbn into models/.

15. Notification side effects interleaved with business logic -- Pub/Sub
    services/order_service.py:44-49,89-100,121-125
    Pattern: Pub/Sub

    _send_email calls are scattered throughout create_order, update_status,
    and cancel_order. Each new side effect (Slack notification, analytics
    event, audit log) requires modifying every method.

    # After -- event-based notification
    EventHandler = Callable[[dict], None]
    subscribers: dict[str, list[EventHandler]] = {}

    def subscribe(event: str, handler: EventHandler) -> None:
        subscribers.setdefault(event, []).append(handler)

    def post_event(event: str, data: dict) -> None:
        for handler in subscribers.get(event, []):
            handler(data)

    # In create_order:
    post_event("order.created", {"order_id": order.id, "email": customer_email})

    # Wire handlers in composition root:
    subscribe("order.created", send_confirmation_email)
    subscribe("order.created", log_order)

---
Summary: 3 critical (layer skip, no DI, no resource management),
7 important (god class, broad catch, missing types, wrong HTTP responses,
missing status codes, raw dicts, deprecated API), 5 suggestions (Strategy,
Registry, StrEnum, split utils, Pub/Sub). The biggest wins would be
introducing a DataInterface Protocol and splitting OrderService.
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
