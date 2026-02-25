# Dependency Injection Reference

Complete guide to dependency injection in Python — from manual parameter passing to Protocol-based abstraction. Covers the distinction between Dependency Injection (pattern) and Dependency Inversion (principle).

> Content derived from Arjan Codes' *Software Designer Mindset* (Depend on Abstractions) and dependency injection tutorials.

---

## 1. What Is Dependency Injection?

Dependency Injection (DI) means supplying dependencies from outside instead of creating them inside. It is a **pattern**, not a framework — just passing parameters.

```python
# BAD — hardwired dependency (creates its own collaborator)
class PaymentProcessor:
    def __init__(self):
        self.authorizer = AuthorizerSMS()  # can't swap, can't test

# GOOD — injected dependency (receives its collaborator)
class PaymentProcessor:
    def __init__(self, authorizer: Authorizer):
        self.authorizer = authorizer  # caller decides which one

# Usage — "single dirty place" where concrete choices are made
processor = PaymentProcessor(AuthorizerSMS())
```

**Key insight:** DI moves the decision about *which concrete implementation to use* out of the class and into a single wiring location.

---

## 2. Dependency Injection vs Dependency Inversion

These are related but distinct concepts:

| | Dependency Injection | Dependency Inversion |
|---|---|---|
| **What** | Pattern | Principle |
| **Goal** | Separate creation from use | Decouple via abstractions |
| **How** | Pass dependencies as parameters | Introduce Protocol/ABC layer |
| **Relationship** | DI *enables* DIP | DIP *requires* DI |

```
DI (pass the thing) → enables → DIP (depend on the abstraction, not the concrete)
```

You can do DI without DIP (pass a concrete class). You cannot do DIP without DI (you must pass *something*).

---

## 3. Manual Constructor Injection

The simplest form — pass dependencies via `__init__` or function parameters.

```python
# Constructor injection
class PointOfSaleSystem:
    def __init__(self, payment_processor: PaymentProcessor):
        self.processor = payment_processor

# Function parameter injection
def process_order(order: Order, processor: PaymentProcessor) -> None:
    processor.pay(order.total_price)
```

This works for most Python projects. No framework needed.

---

## 4. Function-Level Injection with Callable

Accept `Callable` type aliases as parameters. Use `functools.partial` for pre-configuration.

```python
from typing import Callable

AuthorizeFunction = Callable[[], bool]

class PaymentProcessor:
    def __init__(self, authorize: AuthorizeFunction):
        self.authorize = authorize

    def pay(self, amount: int) -> None:
        if not self.authorize():
            raise PermissionError("Authorization failed")
        print(f"Paid {amount}")

# Wire with any function that matches the signature
processor = PaymentProcessor(authorize_sms)
processor = PaymentProcessor(authorize_google)
processor = PaymentProcessor(lambda: True)  # for testing
```

**When to use:** When the dependency is a single behavior (one function), not an object with multiple methods.

---

## 5. Protocol-Based Injection (Pythonic DI)

Define a Protocol for what you need. Pass any conforming object — structural typing means no inheritance required.

```python
from typing import Protocol

class Payable(Protocol):
    @property
    def total_price(self) -> int: ...
    def set_status(self, status: PaymentStatus) -> None: ...

class PaymentProcessor:
    def pay_credit(self, payable: Payable, authorize: AuthorizeFunction) -> None:
        if authorize():
            print(f"Processing: {payable.total_price}")
            payable.set_status(PaymentStatus.PAID)

# Any object with total_price and set_status works — no inheritance needed
```

**Important:** The Protocol belongs to the **consumer**, not the implementor. `PaymentProcessor` defines what it needs; `Order` satisfies it without knowing about the Protocol.

---

## 6. The Composition Root

The "single dirty place" where all concrete implementations are chosen and wired together. In a well-designed codebase, this is the **only** place that knows about concrete classes.

**In FastAPI:** The router layer is the composition root.

```python
# routers/rooms.py — composition root
@router.get("/{room_id}", response_model=Room)
def read_room(room_id: str) -> Room:
    session = SessionLocal()
    data_interface = DBInterface(session, DBRoom)  # concrete wiring HERE
    return room_ops.read_room(room_id, data_interface)
```

**In scripts:** `main()` is the composition root.

```python
def main():
    authorizer = AuthorizerSMS()
    processor = CreditPaymentProcessor(security_code="abc")
    order = Order(customer, items)
    processor.pay(order, authorizer)
```

**Quality test:** If you find concrete class instantiations scattered across multiple files, the design needs refactoring. All wiring should converge to one location.

---

## 7. The Bridge Pattern (Two Axes of Variation)

When you have **two independent dimensions** that vary, DI naturally produces the Bridge pattern.

```python
# Payment methods: Debit, Credit, PayPal (axis 1)
# Authorization methods: SMS, Google, Robot (axis 2)
# These vary independently — any combination should work

class PaymentProcessor(Protocol):
    def pay(self, payable: Payable, authorize: AuthorizeFunction) -> None: ...

class DebitPaymentProcessor:
    def pay(self, payable: Payable, authorize: AuthorizeFunction) -> None: ...

class CreditPaymentProcessor:
    def pay(self, payable: Payable, authorize: AuthorizeFunction) -> None: ...

# Wire any combination in the composition root
processor = CreditPaymentProcessor()
processor.pay(order, authorize_sms)      # Credit + SMS
processor.pay(order, authorize_google)   # Credit + Google
```

---

## 8. Testing with DI

With DI, testing is straightforward — swap real implementations for stubs.

```python
# Production
processor = PaymentProcessor(AuthorizerSMS())

# Test — inject a mock that always authorizes
processor = PaymentProcessor(lambda: True)

# Test — inject a mock that always fails
processor = PaymentProcessor(lambda: False)
```

For the DataInterface pattern used in this plugin's architecture:

```python
# Production (in router — composition root)
data_interface = DBInterface(session, DBRoom)
room = room_ops.read_room(room_id, data_interface)

# Test (no database needed)
stub = DataInterfaceStub()
stub.data["room-1"] = {"id": "room-1", "number": "101", "size": 2, "price": 150}
room = room_ops.read_room("room-1", stub)
assert room.price == 150
```

---

## 9. Anti-Patterns

### Service Locator

```python
# BAD — hidden dependency, hard to trace
class PaymentProcessor:
    def pay(self, order):
        authorizer = ServiceLocator.get(Authorizer)  # where does this come from?
```

Use explicit parameter injection instead.

### Injecting Too Much

```python
# BAD — passes the entire config object
def process(config: AppConfig): ...

# GOOD — passes only what's needed
def process(api_url: str, timeout: int): ...
```

### Creating Dependencies in __init__

```python
# BAD — hardwired
class OrderService:
    def __init__(self):
        self.db = PostgresDatabase()
        self.mailer = SMTPMailer()

# GOOD — injected
class OrderService:
    def __init__(self, db: Database, mailer: Mailer):
        self.db = db
        self.mailer = mailer
```

**Detection:** `self.x = ConcreteClass()` inside `__init__`. If you see this, the class can't be tested without its concrete dependency.

> Content inspired by Arjan Codes' *Software Designer Mindset* and dependency injection tutorials.
