# Design Principles Reference

The seven principles that govern all code decisions. Apply them in this order of priority.

## 1. High Cohesion

Every code unit (class, function, method) has a single, well-defined responsibility.

### Diagnostic Signs of Low Cohesion

- A class with many unrelated responsibilities (e.g., `Order` that also processes payments)
- A method that branches on a type/flag argument to do entirely different things
- Duplicated structural patterns (same logic repeated for different data)
- A function that handles I/O, computation, and presentation all at once

### Refactoring Techniques

**Extract Class:** When a class does two things, move the secondary responsibility into its own class.

```python
# BEFORE: Order handles both data AND payment
class Order:
    def add_item(self, name, quantity, price): ...
    def pay(self, payment_type, security_code): ...  # doesn't belong

# AFTER: Separate concerns
class Order:
    def add_item(self, name, quantity, price): ...
    def set_status(self, status): ...

class PaymentProcessor:
    def pay_debit(self, order, security_code): ...
    def pay_credit(self, order, security_code): ...
```

**Extract Function:** When a function does multiple things, pull each concern into its own function.

```python
# BEFORE: monolithic main
def main():
    # read input, compute, print — all mixed together
    vehicle_type = input(...)
    # ... 30 lines of mixed logic

# AFTER: each concern is its own function
def read_vehicle_type() -> str: ...
def compute_rental_cost(vehicle: Vehicle, days: int, km: int) -> int: ...

def main():
    vehicle_type = read_vehicle_type()
    vehicle = VEHICLE_DATA[vehicle_type]
    cost = compute_rental_cost(vehicle, days, km)
    print(f"Cost: ${cost}")
```

**Replace Conditional with Separate Methods:** When a method branches on a type flag, split into distinct methods.

```python
# BEFORE
def pay(self, order, payment_type, security_code):
    if payment_type == "debit": ...
    elif payment_type == "credit": ...

# AFTER
def pay_debit(self, order, security_code): ...
def pay_credit(self, order, security_code): ...
```

---

## 2. Low Coupling

Minimize dependencies between classes, functions, and modules.

### Seven Types of Coupling (worst to best)

1. **Content Coupling** — One function directly modifies another class's internals. Fix: move the function into the class.
2. **Global Coupling** — Functions share global data. Fix: pass data as parameters, make globals local to composition root.
3. **External Coupling** — Dependency on external APIs. Fix: wrap behind an abstraction (Protocol).
4. **Control Coupling** — Passing flags/callbacks to control another module's flow. Sometimes acceptable.
5. **Stamp Coupling** — Depending on a data structure but using only part of it. Fix: pass only what the function needs.
6. **Data Coupling** — Sharing data via parameters. Normal and expected.
7. **Message Coupling** — Communication via events/messages. Lightest coupling.

### Coupling Examples (Before/After)

**Content Coupling** — directly accessing another class's private state:

```python
# BAD: reaches into Account internals
def pay_service_fee(account: Account, payment_type: PaymentType) -> None:
    account._balance -= SERVICE_FEES[payment_type]

# GOOD: use the class's own method
def pay_service_fee(account: Account, payment_type: PaymentType) -> None:
    account.withdraw_unsafe(SERVICE_FEES[payment_type])
```

**Global Coupling** — module-level constants used directly by functions:

```python
# BAD: function depends on global state
API_URL = "https://api.company.com"
TOKEN = "a3f5c7e8..."

def make_request(path: str, data: dict | None = None) -> None:
    headers = {"Authorization": f"Bearer {TOKEN}"}
    fullpath = f"{API_URL}/{path}"

# GOOD: encapsulate configuration in a dataclass
@dataclass
class APIClient:
    api_url: str
    token: str

    def post(self, path: str, data: dict | None = None) -> None:
        headers = {"Authorization": f"Bearer {self.token}"}
        fullpath = f"{self.api_url}/{path}"
```

**Stamp Coupling** — passing an entire object when only part is needed:

```python
# BAD: log_transaction receives full Transaction but only uses 3 fields
def log_transaction(transaction: Transaction) -> None:
    print(f"Logging {transaction.transaction_type} ID {transaction.transaction_id}")

# GOOD: accept a Protocol with only the fields needed
class LoggableTransaction(Protocol):
    transaction_id: int
    transaction_type: TransactionType
    timestamp: datetime

def log_transaction(transaction: LoggableTransaction) -> None:
    print(f"Logging {transaction.transaction_type} ID {transaction.transaction_id}")
```

### Law of Demeter (Principle of Least Knowledge)

A unit of code should only talk to closely related units. Never chain through multiple objects.

```python
# BAD: main reaches through rental to vehicle
total = rental.vehicle.total_price(rental.days, rental.additional_km)

# GOOD: rental exposes a property that delegates internally
total = rental.total_price
```

### Decoupling Techniques

- **Move method to the class that owns the data** — `add_item(order, ...)` becomes `order.add_item(...)`
- **Return values instead of side effects** — Return computed result, let caller handle I/O
- **Pass only what a function needs** — `read_vehicle_type(vehicle_types: list[str])` not the entire dict
- **Extract magic numbers into configurable attributes** — `km_free_limit: int = 100`
- **Replace globals with local variables in composition root** — `VEHICLE_DATA` constant becomes local `vehicle_data`

---

## 3. Depend on Abstractions

Use Protocol classes and Callable type aliases to decouple from concrete implementations.

### Protocol for Object Abstractions

```python
from typing import Protocol

class Payable(Protocol):
    total_price: int
    def set_status(self, status: PaymentStatus) -> None: ...
```

- No inheritance needed in implementing classes — structural typing handles matching
- The Protocol belongs conceptually to the **consumer** (the function that uses it), not the implementor
- Implementing classes satisfy the Protocol by having the right methods/attributes

### Callable for Function Abstractions

```python
from typing import Callable

AuthorizeFunction = Callable[[], bool]

class PaymentProcessor:
    def __init__(self, authorize: AuthorizeFunction):
        self.authorize = authorize
```

Pass the function reference, not call it: `PaymentProcessor(authorize_sms)`.

### When to Use ABC vs Protocol

| Use ABC when... | Use Protocol when... |
|---|---|
| Shared implementation needed (instance variables in superclass) | Working with third-party code you cannot modify |
| Strong hierarchical grouping is intentional | Interface segregation needed (split into small contracts) |
| Error at instantiation time desired | Loose coupling preferred |
| | Error at usage/call-site acceptable |

### The Emergent Patterns Insight

Do not start from design patterns and try to apply them. Start from identifying coupling, then use abstraction mechanisms to decouple. The right patterns emerge naturally:

- Callable type alias → Strategy Pattern emerges
- Protocol + separate implementations → Bridge Pattern emerges
- Dictionary mapping to callables → Factory Pattern emerges
- Injecting dependencies from outside → DI Pattern emerges

---

## 4. Composition over Inheritance

Inheritance is the strongest coupling that exists. Use composition instead.

### The Composition Pattern

1. **Identify duplicated behavior** across classes (e.g., commission logic in multiple employee types)
2. **Extract into a standalone class** with a Protocol interface:

```python
class PaymentSource(Protocol):
    def compute_pay(self) -> int: ...

@dataclass
class DealBasedCommission:
    commission: int = 100
    deals_landed: int = 0
    def compute_pay(self) -> int:
        return self.commission * self.deals_landed

@dataclass
class HourlyContract:
    hourly_rate: int
    hours_worked: float
    def compute_pay(self) -> int:
        return int(self.hourly_rate * self.hours_worked)
```

3. **Use a list of composed objects** on the consuming class:

```python
@dataclass
class Employee:
    name: str
    id: int
    payment_sources: list[PaymentSource] = field(default_factory=list)

    def compute_pay(self) -> int:
        return sum(source.compute_pay() for source in self.payment_sources)
```

4. **Wire together in one place** (the composition root):

```python
sarah = Employee(name="Sarah", id=47)
sarah.add_payment_source(SalariedContract(monthly_salary=5000))
sarah.add_payment_source(DealBasedCommission(commission=100, deals_landed=10))
```

### Rules for Inheritance

- Only use for defining abstractions: one level deep (ABC/Protocol → concrete)
- Keep hierarchies flat — never go several levels deep
- Never use mixins (MRO issues, type checker incompatibility, breaks "is-a" semantics)

---

## 5. Separate Creation from Use

Object creation and object usage are distinct responsibilities.

### Dictionary Mapping Pattern

Replace if/elif chains with dictionary lookups:

```python
# BEFORE
if export_quality == "low":
    factory = LowQualityExporter()
elif export_quality == "high":
    factory = HighQualityExporter()

# AFTER
factories: dict[str, ExporterFactory] = {
    "low": LowQualityExporter(),
    "high": HighQualityExporter(),
    "master": MasterQualityExporter(),
}
factory = factories[export_quality]
```

### Creator Functions (Pythonic Factory)

When different types need different creation logic:

```python
def create_credit_processor() -> PaymentProcessor:
    security_code = input("Security code: ")
    return CreditPaymentProcessor(security_code)

payment_processors: dict[str, Callable[[], PaymentProcessor]] = {
    "credit": create_credit_processor,
    "debit": lambda: DebitPaymentProcessor(),
    "paypal": create_paypal_processor,
}

def read_payment_processor() -> PaymentProcessor:
    choice = read_choice("How to pay?", list(payment_processors.keys()))
    return payment_processors[choice]()
```

### The "Single Dirty Place"

A well-designed system has one conceptual place where all concrete wiring happens — the composition root. In a standalone script, this is the `main()` function. In FastAPI, the **router layer** serves as the composition root — the topmost layer where concrete database implementations are chosen and injected into operations.

For production FastAPI apps, use `Depends()` to centralize dependency creation instead of repeating it in every endpoint:

```python
from fastapi import Depends
from sqlalchemy.orm import Session

def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def get_room_interface(session: Session = Depends(get_db)) -> DBInterface:
    return DBInterface(session, DBRoom)

@router.get("/", response_model=list[Room])
def read_all_rooms(data_interface: DBInterface = Depends(get_room_interface)):
    return room_ops.read_all_rooms(data_interface)
```

This keeps the wiring in one place (the dependency provider functions) and makes testing easier via dependency overrides.

### Open-Closed Principle

The dictionary-mapping approach means the system is open for extension (add new entries) but closed for modification (existing code untouched).

---

## 6. Start with the Data

The shape of data structures directly determines architecture quality.

### Information Expert Principle (GRASP) & Tell, Don't Ask

Place behavior on the class that has the data needed to perform it. Instead of retrieving data from an object and computing externally, **tell** the object to do the computation itself — it is closest to the data.

```python
# BAD (Ask): pull data out, compute externally
total = rental.vehicle.total_price(rental.days, rental.additional_km)

# GOOD (Tell): tell the object to compute it
@dataclass
class RentalContract:
    vehicle: Vehicle
    days: int
    additional_km: int

    @property
    def total_price(self) -> int:
        return self.vehicle.total_price(self.days, self.additional_km)
```

### Data Structure Smells

- **Prefixed fields** (`customer_name`, `customer_email`) → Extract a `Customer` class
- **Parallel lists** (`items: list[str]`, `quantities: list[int]`, `prices: list[int]`) → Extract a `LineItem` dataclass
- **Method with many parameters** → The method is far from its data; move it closer
- **Chains of attribute access** (`a.b.c.method()`) → Add a method at the intermediate layer

### Choosing Data Structures

| Dominant Operation | Best Structure |
|---|---|
| Search by key | `dict` (O(1) hash lookup) |
| Ordered iteration | `list` |
| Grouping 2-3 related values | `tuple` |
| Fixed set of valid options | `Enum` |
| Unique elements | `set` |

---

## 7. Keep Things Simple

### DRY — Don't Repeat Yourself

Extract shared logic into reusable functions. But apply **AHA (Avoid Hasty Abstractions)** — do not over-generalize unrelated code or create "god functions" with too many parameters.

### KISS — Keep It Stupidly Simple

Use the simplest design that meets current requirements. If two class attributes solve the problem, do not build a strategy pattern with polymorphic classes.

### YAGNI — You Ain't Gonna Need It

Implement only what is needed now. Every extra feature needs tests and increases maintenance burden. But YAGNI does not mean "write crappy code" — invest effort in clean structure, not speculative features.
