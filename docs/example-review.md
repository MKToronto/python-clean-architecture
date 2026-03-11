# Example Output

> From running `/review-architecture` against a test bookstore-api project. See the [color-coded version](https://mktoronto.github.io/python-clean-architecture/) on the landing page.

```
Architecture Review: python-clean-architecture/testing/

Architecture Summary

Layers
──────
API:        routers/books.py, routers/orders.py
Logic:      services/book_service.py, services/order_service.py
Database:   db/database.py
Models:     models/book.py, models/order.py
Unclear:    utils/helpers.py (mixed — formatting, validation, AND direct DB access)

Dependency Flows
────────────────
routers/books.py → services/book_service.py → db/database.py      ✓
routers/orders.py → services/order_service.py → db/database.py    ✓
routers/orders.py → db/database.py                                 ⚠ layer skip
utils/helpers.py → db/database.py                                  ⚠ unclear layer

Layer Violations
────────────────
⚠ routers/orders.py:2,21-32 — imports and queries DB directly, bypassing service
⚠ utils/helpers.py:1,16,31 — utility module directly accesses database layer

Missing Abstraction Layer
─────────────────────────
No DataInterface Protocol exists. Both services import concrete SessionLocal and
ORM models directly. Operations cannot be tested without a real database.

---
What Works Well

- Create/Read model separation — models/book.py correctly separates BookCreate
  (input) from Book (output with id). Same pattern in models/order.py.
- Router prefixing in main.py — Clean FastAPI setup with /books and /orders
  prefixes and tags.
- get_db() generator exists in db/database.py:31-36 — A proper session dependency
  is defined, even though nothing currently uses it.
- Service layer exists — The project has the right instinct to separate routers
  from business logic. The three-layer structure is present in skeleton form.

---
Findings by Severity

Critical

1. OrderService is a God Class — 7+ responsibilities in one class
   File: services/order_service.py:6-177
   Principles: P1 High Cohesion, P7 Keep Things Simple
   Pattern: Extract Class — split into focused collaborators

   The docstring says it all: "Handles orders, payments, inventory, notifications,
   discounts, and shipping." This class does order CRUD, discount calculation, email
   notifications, inventory management, logging, refund processing, and shipping
   calculation.

   Fix: Extract each responsibility into its own module:

   # services/discount.py
   from typing import Callable

   DiscountFunction = Callable[[float, int], float]

   DISCOUNT_RULES: dict[str, float] = {
       "bulk": 0.8,
       "medium": 0.9,
   }

   QUANTITY_THRESHOLDS: list[tuple[int, str]] = [
       (10, "bulk"),
       (5, "medium"),
   ]

   def apply_quantity_discount(total: float, quantity: int) -> float:
       for threshold, tier in QUANTITY_THRESHOLDS:
           if quantity >= threshold:
               return total * DISCOUNT_RULES[tier]
       return total

   # services/order_service.py — reduced to order CRUD only
   from typing import Protocol

   class OrderDataInterface(Protocol):
       def create(self, book_id: int, quantity: int,
                  customer_email: str, total: float) -> dict: ...
       def get(self, order_id: int) -> dict | None: ...
       def update_status(self, order_id: int, status: str) -> dict | None: ...

   def create_order(
       data_interface: OrderDataInterface,
       book_id: int,
       quantity: int,
       customer_email: str,
       compute_discount: DiscountFunction = apply_quantity_discount,
   ) -> dict:
       book = data_interface.get_book(book_id)
       if not book:
           raise BookNotFoundError(f"Book {book_id} not found")
       total = compute_discount(book["price"] * quantity, quantity)
       return data_interface.create(book_id, quantity, customer_email, total)

---
2. No DataInterface Protocol — services tightly coupled to concrete DB
   File: services/book_service.py:1, services/order_service.py:3
   Principles: P3 Depend on Abstractions, P2 Low Coupling
   Pattern: Repository pattern — Protocol-based DataInterface

   Every service function directly imports SessionLocal and ORM models. This makes
   unit testing impossible without a real database and prevents swapping storage
   backends.

   Fix:

   # db/data_interface.py
   from typing import Protocol

   class BookDataInterface(Protocol):
       def create(self, title: str, author: str, isbn: str, price: float) -> dict: ...
       def get_all(self) -> list[dict]: ...
       def get_by_id(self, book_id: int) -> dict | None: ...
       def search_by_title(self, query: str) -> list[dict]: ...

   # services/book_service.py — accepts Protocol, not concrete DB
   def create_book(data_interface: BookDataInterface, data: BookCreate) -> Book:
       return data_interface.create(**data.model_dump())

   def get_all_books(data_interface: BookDataInterface) -> list[dict]:
       return data_interface.get_all()

   # routers/books.py — composition root wires concrete implementation
   from db.database import DBBookInterface

   @router.post("/")
   def add_book(data: BookCreate, db: Session = Depends(get_db)):
       data_interface = DBBookInterface(db)
       return create_book(data_interface, data)

---
3. Router bypasses service layer — direct DB access
   File: routers/orders.py:2,21-32
   Principles: P2 Low Coupling, P1 High Cohesion

   The read_order endpoint directly imports SessionLocal and OrderModel and queries
   the database, even though OrderService.get_order() already does this.

   Fix: Remove the DB imports and use the service:

   @router.get("/{order_id}")
   def read_order(order_id: int):
       result = order_service.get_order(order_id)
       if not result:
           raise HTTPException(status_code=404, detail="Order not found")
       return result

---
4. Broad exception catching silently swallows errors
   File: services/order_service.py:154-164
   Principles: P7 Keep Things Simple
   Pattern: Custom exceptions — catch specific types only

   # CURRENT: swallows everything including NameError, AttributeError
   except Exception:
       pass

   This hides real bugs. If smtplib raises a ConnectionRefusedError, you'd never
   know emails aren't being sent.

   Fix:

   def _send_email(self, to: str, subject: str, body: str) -> None:
       try:
           msg = MIMEText(body)
           msg["Subject"] = subject
           msg["To"] = to
           msg["From"] = "noreply@bookstore.com"
           server = smtplib.SMTP("localhost", 587)
           server.send_message(msg)
           server.quit()
       except (smtplib.SMTPException, ConnectionRefusedError, OSError) as e:
           logging.warning("Failed to send email to %s: %s", to, e)

---
Important

5. No type hints on most functions
   Files: services/book_service.py:15,25,34, services/order_service.py:9,66,80,105,133,139,
   utils/helpers.py:4,15,22,30
   Principles: P7 Keep Things Simple (type hints are documentation)

   get_all_books(), get_book(book_id), search_books(query), and nearly every OrderService
   method lack parameter and return type annotations. This hurts IDE support and makes
   the contract unclear.

   Fix (example):

   def get_all_books() -> list[dict[str, Any]]: ...
   def get_book(book_id: int) -> dict[str, Any] | None: ...
   def search_books(query: str) -> list[dict[str, Any]]: ...

---
6. Manual session management leaks on exceptions
   Files: services/book_service.py:6-12, services/order_service.py:10-57 (every method)
   Principles: P2 Low Coupling
   Pattern: Context manager for resource management

   Every function does db = SessionLocal() then db.close() at the end. If any exception
   occurs between open and close, the session leaks. The get_db() generator in database.py
   already solves this but is never used.

   Fix: Use the existing get_db() as a FastAPI dependency, or use a context manager:

   from contextlib import contextmanager

   @contextmanager
   def get_session():
       db = SessionLocal()
       try:
           yield db
       finally:
           db.close()

   # Usage
   def get_all_books() -> list[dict]:
       with get_session() as db:
           books = db.query(BookModel).all()
           return [{"id": b.id, ...} for b in books]

---
7. Order status uses bare str — should be an Enum
   File: models/order.py:16, services/order_service.py:89,91,111,114
   Principles: P6 Start with the Data
   Pattern: Enum for fixed options (Rule 1: No Type Abuse)

   Status values "pending", "shipped", "delivered", "cancelled" are strewn across
   the codebase as string literals — typo-prone and without IDE autocomplete.

   Fix:

   from enum import Enum

   class OrderStatus(str, Enum):
       PENDING = "pending"
       SHIPPED = "shipped"
       DELIVERED = "delivered"
       CANCELLED = "cancelled"

   class Order(BaseModel):
       # ...
       status: OrderStatus

---
8. Errors returned as dicts instead of exceptions
   Files: routers/books.py:21-22, routers/orders.py:14,24-25,
   services/order_service.py:112-113
   Principles: P3 Depend on Abstractions
   Pattern: Custom exception classes — raise at logic layer, catch at API boundary

   Returning {"error": "Book not found"} as a 200 response is an API anti-pattern.
   Clients can't distinguish success from failure by HTTP status code.

   Fix:

   # services/exceptions.py
   class BookNotFoundError(Exception): ...
   class OrderNotFoundError(Exception): ...
   class InvalidOrderStateError(Exception): ...

   # services/order_service.py
   def cancel_order(self, order_id: int) -> dict:
       ...
       if order.status != OrderStatus.PENDING:
           raise InvalidOrderStateError("Can only cancel pending orders")

   # routers/orders.py
   from fastapi import HTTPException

   @router.delete("/{order_id}")
   def cancel(order_id: int):
       try:
           return order_service.cancel_order(order_id)
       except OrderNotFoundError:
           raise HTTPException(status_code=404, detail="Order not found")
       except InvalidOrderStateError as e:
           raise HTTPException(status_code=409, detail=str(e))

---
9. utils/helpers.py is a dumping ground with mixed concerns
   File: utils/helpers.py:1-38
   Principles: P1 High Cohesion, P2 Low Coupling
   Pattern: Rule 16 — Avoid generic package names

   This file has formatting (format_price), DB queries (get_bestsellers,
   generate_report), and validation (validate_isbn) — three unrelated
   responsibilities. The name utils/helpers is a code smell per Rule 16.

   Fix: Move each function to where it belongs:
   - format_price → models/book.py or a formatting module
   - get_bestsellers → services/book_service.py
   - validate_isbn → models/book.py (as a Pydantic validator)
   - generate_report → services/report_service.py

---
Suggestions

10. Discount logic uses redundant if/elif — replace with dict mapping
    File: services/order_service.py:19-31
    Principles: P5 Separate Creation from Use
    Pattern: Strategy pattern — dict mapping replaces if/elif

    The discount code first maps quantity to a discount type string, then maps that
    string to a multiplier — two cascaded if/elif chains.

    Fix:

    DISCOUNT_TIERS: list[tuple[int, float]] = [
        (10, 0.8),   # 20% off for 10+
        (5, 0.9),    # 10% off for 5+
    ]

    def compute_discount(total: float, quantity: int) -> float:
        for min_qty, multiplier in DISCOUNT_TIERS:
            if quantity >= min_qty:
                return total * multiplier
        return total

---
11. Magic numbers throughout
    Files: services/order_service.py:19,21,26-27,145-150,160, utils/helpers.py:23-26
    Principles: P7 Keep Things Simple (Rule 11: No Magic Numbers)

    0.8, 0.9, 50, 25, 4.99, 9.99, 587, 10, 5, 13, 10 — all unnamed literals.

    Fix: Extract into named constants or configurable attributes:

    FREE_SHIPPING_THRESHOLD = 50.0
    REDUCED_SHIPPING_THRESHOLD = 25.0
    REDUCED_SHIPPING_COST = 4.99
    STANDARD_SHIPPING_COST = 9.99
    SMTP_PORT = 587

---
12. format_price if/elif chain — use dict mapping
    File: utils/helpers.py:4-12
    Principles: P5 Separate Creation from Use
    Pattern: Dict mapping replaces if/elif

    Fix:

    CURRENCY_SYMBOLS: dict[str, str] = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
    }

    def format_price(amount: float, currency: str) -> str:
        symbol = CURRENCY_SYMBOLS.get(currency)
        if symbol:
            return f"{symbol}{amount:.2f}"
        return f"{amount:.2f} {currency}"

---
13. Inconsistent return types in book_service.py
    File: services/book_service.py:5-12 vs 15-22
    Principles: P1 High Cohesion

    create_book() returns a Book Pydantic model, but get_all_books() returns
    list[dict] and get_book() returns dict | None. Pick one convention —
    preferably return Pydantic models consistently.

---
14. Deprecated Pydantic v1 API
    File: services/book_service.py:7

    data.dict() is deprecated in Pydantic v2. Use data.model_dump().

---
15. Module-level OrderService() instantiation
    File: routers/orders.py:7
    Principles: P5 Separate Creation from Use

    order_service = OrderService() is created at module import time as global
    state. Should be created via FastAPI's Depends() for testability.

---
Summary

┌─────────────┬───────┬─────────────────────────────────────────┐
│  Severity   │ Count │               Key Themes                │
├─────────────┼───────┼─────────────────────────────────────────┤
│ Critical    │ 4     │ God class, no abstractions, layer skip, │
│             │       │ swallowed exceptions                    │
├─────────────┼───────┼─────────────────────────────────────────┤
│             │       │ Missing type hints, session leaks,      │
│ Important   │ 5     │ string status, dict errors,             │
│             │       │ dumping-ground utils                    │
├─────────────┼───────┼─────────────────────────────────────────┤
│             │       │ Dict mappings, magic numbers,           │
│ Suggestions │ 6     │ inconsistent returns, deprecated API,   │
│             │       │ global state                            │
└─────────────┴───────┴─────────────────────────────────────────┘

Top 3 priorities:
1. Introduce a DataInterface Protocol and inject it — this unblocks testability
   for everything else
2. Break up OrderService into focused modules (order CRUD, discounts, notifications)
3. Add OrderStatus enum and custom exception classes to replace string errors and
   dict error returns
```
