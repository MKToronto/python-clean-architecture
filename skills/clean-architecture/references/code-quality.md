# Code Quality Reference

22 code quality rules derived from common design mistakes, plus a code review checklist.

## The 22 Design Rules

### 1. No Type Abuse

Do not use a type for something it was not designed for. Use enums for fixed option sets, not strings. Use integers for money (cents), not floats.

```python
# BAD
status = "active"  # typo-prone, no IDE support

# GOOD
class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
```

### 2. No Vague Identifiers

Names should be specific and descriptive. Avoid `data`, `info`, `manager`, `handler`, `utils`, `helper`, `processor`.

```python
# BAD
def process_data(data): ...

# GOOD
def compute_rental_cost(vehicle: Vehicle, days: int, km: int) -> int: ...
```

### 3. No Flags as Parameters

Boolean parameters that change function behavior are a code smell. Split into separate functions.

```python
# BAD
def create_user(name: str, is_admin: bool): ...

# GOOD
def create_user(name: str): ...
def create_admin(name: str): ...
```

### 4. No Deep Nesting

More than 2-3 levels of indentation makes code hard to follow. Use guard clauses (early returns) and extract helper functions.

```python
# BAD
def process(order):
    if order:
        if order.items:
            for item in order.items:
                if item.price > 0:
                    # actual logic buried 4 levels deep

# GOOD
def process(order):
    if not order or not order.items:
        return
    for item in order.items:
        process_item(item)

def process_item(item):
    if item.price <= 0:
        return
    # actual logic at shallow depth
```

### 5. Tell, Don't Ask

Do not interrogate an object's state and then act on it from outside. Tell the object to do it.

```python
# BAD (ask then act)
if order.status == "open":
    order.status = "paid"
    send_receipt(order)

# GOOD (tell)
order.mark_as_paid()  # encapsulates state change + side effects
```

### 6. No Parallel Data Structures

Multiple lists/dicts that must stay in sync indicate a missing composite type.

```python
# BAD
names = ["Widget", "Gadget"]
quantities = [3, 5]
prices = [100, 200]

# GOOD
@dataclass
class LineItem:
    name: str
    quantity: int
    price: int

items = [LineItem("Widget", 3, 100), LineItem("Gadget", 5, 200)]
```

### 7. No God Classes

A class that does everything. Split into focused classes with single responsibilities.

### 8. No Feature Envy

A method that uses more data from another class than its own. Move the method to the class it envies.

### 9. No Bare Primitives

Using raw primitives (str, int) where a domain type is needed. Create value objects.

```python
# BAD
def send_email(to: str): ...  # any string? file path? URL?

# GOOD
@dataclass
class EmailAddress:
    value: str
    def __post_init__(self):
        if "@" not in self.value:
            raise ValueError(f"Invalid email: {self.value}")
```

### 10. No Dead Code

Remove unused functions, variables, imports, and commented-out code. Version control preserves history. This includes dead imports (`import os` when os is never used), explicit `return None` at the end of void functions (Python does this implicitly), and `class Foo(object):` in Python 3 (just use `class Foo:`).

### 11. No Magic Numbers

Use named constants or configurable attributes instead of literal values. This includes semantic constants for data representations, not just numeric parameters.

```python
# BAD
if km > 100:
    paid_km = km - 100

# GOOD
KM_FREE_LIMIT = 100
if km > KM_FREE_LIMIT:
    paid_km = km - KM_FREE_LIMIT

# Also extract semantic constants (not just numbers)
# BAD
self.grid[row][col] = "O"

# GOOD
HIDDEN = "O"
SHIP = "S"
GUESS = "X"
self.grid[row][col] = HIDDEN
```

### 12. No Broad Exception Catching

Never use bare `except:` or `except Exception:`. Always catch specific exception types.

```python
# BAD
try:
    blog = fetch_blog(blog_id)
except Exception:
    return 404  # catches everything, masks real bugs

# GOOD
try:
    blog = fetch_blog(blog_id)
except NotFoundError:
    return 404
except NotAuthorizedError:
    return 403
```

### 13. Use Context Managers for Resources

Encapsulate resource lifecycle (open/close) in context managers.

```python
class SQLite:
    def __init__(self, file: str = "app.db"):
        self.file = file

    def __enter__(self):
        self.connection = sqlite3.connect(self.file)
        return self.connection.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()

# Usage
with SQLite("app.db") as cursor:
    cursor.execute(query)
```

### 14. No Mutable Default Arguments

Never use mutable objects as default parameter values.

```python
# BAD — shared list across all instances
def add_items(items: list = []): ...

# GOOD
def add_items(items: list | None = None):
    if items is None:
        items = []

# BEST (with dataclasses)
items: list[str] = field(default_factory=list)
```

### 15. No Wildcard Imports

Always import specific items. Wildcards destroy traceability.

```python
# BAD
from models import *

# GOOD
from models.room import Room, RoomCreate
```

### 16. Avoid Generic Package Names

Do not name packages `utils`, `helpers`, `managers`, `handlers`. These become dumping grounds. Use domain-specific names.

```python
# BAD
utils/
    helpers.py
    misc.py

# GOOD
pricing/
    compute.py
importers/
    csv_importer.py
```

### 17. Folder Structure Mirrors Architecture

The directory layout should reflect the software architecture pattern in use.

```
# Layered architecture
routers/
    operations/
    db/
    models/

# MVC
src/
    models/
    views/
    controllers/
```

### 18. No isinstance Checks for Dispatch

Using `isinstance` to decide what to do with an object signals a missing method on the object itself. Move the behavior into the class hierarchy or use a strategy dict.

```python
# BAD: external dispatch based on type
def pay_employee(employee: Employee):
    if isinstance(employee, SalariedEmployee):
        print(f"Paying {employee.name} salary of {employee.monthly_salary}")
    elif isinstance(employee, HourlyEmployee):
        print(f"Paying {employee.name} for {employee.hours_worked} hours")

# GOOD: each class implements its own pay method
class Employee(Protocol):
    def pay(self) -> None: ...

employee.pay()
```

### 19. No Overloaded Classes

When a class has too many instance variables, it likely holds multiple responsibilities. Extract cohesive groups into separate classes.

```python
# BAD: Order knows everything about the customer
@dataclass
class Order:
    customer_name: str
    customer_address: str
    customer_city: str
    customer_email: str
    items: list[LineItem] = field(default_factory=list)

# GOOD: separate Customer from Order
@dataclass
class Customer:
    name: str
    address: str
    city: str
    email: str

@dataclass
class Order:
    customer: Customer
    items: list[LineItem] = field(default_factory=list)
```

### 20. No Asymmetric Naming

When multiple classes do the same kind of thing, name the methods consistently. Use Python dunder methods when they exist.

```python
# BAD: inconsistent string conversion names
class VehicleModelInfo:
    def get_formatted_info(self) -> str: ...

class Vehicle:
    def to_display_string(self) -> str: ...

# GOOD: use __str__ consistently
class VehicleModelInfo:
    def __str__(self) -> str: ...

class Vehicle:
    def __str__(self) -> str: ...
```

### 21. No Misleading Method Names

Method names must accurately describe what the method does. `create_X` should create and return X. `add_X` should add X to a collection. `get_X` should retrieve X.

```python
# BAD: "create_line_item" suggests it creates and returns,
# but it actually appends to an internal list
def create_line_item(self, name: str, quantity: int, price: int) -> None:
    self.items.append(name)

# GOOD: name matches behavior
def add_line_item(self, item: LineItem) -> None:
    self.items.append(item)
```

### 22. No Hardwired Initialization Sequences

If forgetting to call a setup method breaks the system, the sequence should be encapsulated. Use a factory method or `__init__` to guarantee proper setup.

```python
# BAD: caller must remember to call connect after creation
processor = StripePaymentProcessor()
processor.connect_to_service("https://api.stripe.com")  # forget this = crash

# GOOD: factory method guarantees complete initialization
class StripePaymentProcessor:
    @staticmethod
    def create(url: str) -> "StripePaymentProcessor":
        processor = StripePaymentProcessor()
        processor.connect_to_service(url)
        return processor
```

---

## Code Review Checklist

When reviewing Python code, check for:

### Structure
- [ ] Each file/class has a single responsibility
- [ ] No file exceeds ~200 lines (split if larger)
- [ ] No function exceeds ~40 lines
- [ ] Import structure is clean (no wildcards, no circular imports)
- [ ] Folder structure reflects architecture

### Naming
- [ ] No vague identifiers (data, info, manager, utils)
- [ ] snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants
- [ ] Names reflect what the thing IS, not what it does generically

### Types and Data
- [ ] Type hints on all function parameters and return types
- [ ] Enums for fixed option sets (not strings)
- [ ] Dataclasses for structured data
- [ ] No parallel data structures
- [ ] No mutable default arguments

### Design
- [ ] Each layer depends only on the layer below
- [ ] Operations accept Protocol parameters (not concrete DB classes)
- [ ] No Law of Demeter violations (chains of `a.b.c.method()`)
- [ ] Composition used instead of deep inheritance
- [ ] One composition root (router/main) where concrete wiring happens

### Error Handling
- [ ] Custom domain exceptions (not generic Exception)
- [ ] Specific exception catches only
- [ ] Context managers for resource management
- [ ] No bare except clauses

### Simplicity
- [ ] No speculative features (YAGNI)
- [ ] No over-engineered patterns for simple problems (KISS)
- [ ] Shared logic extracted (DRY) but not over-generalized (AHA)
- [ ] No dead code or commented-out code
