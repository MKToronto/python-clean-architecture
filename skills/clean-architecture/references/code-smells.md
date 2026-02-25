# Code Smells and Anti-Patterns Reference

A catalog of code smells — recurring indicators that something in the code needs a closer look. Not every smell is a bug, but each one hints at a design problem that may cause issues as the codebase grows. Use this reference to detect problems early and apply targeted fixes.

> Content derived from Arjan Codes' *Software Designer Mindset* (Design Wins) and *Code Smells* videos.

---

## What Is a Code Smell?

A code smell is a surface-level indicator of a deeper design problem. It is not a bug — the code may work perfectly — but it signals that something could be improved. The pragmatic approach: assess each smell in context, not as an absolute rule.

---

## 1. Naming & Identity Smells

### 1.1 Type Abuse

Using a broad type to represent constrained values. Strings and ints used where Enums belong.

```python
# BAD
user = User("John", "Doe", "slacker")  # any string accepted for role

# GOOD
class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"

user = User("John", "Doe", Role.USER)  # invalid values caught at type-check time
```

**Detection:** String/int parameters that accept only specific values in business logic. If/elif chains comparing against string literals.

### 1.2 Vague Identifiers

Names that don't communicate intent: `data`, `info`, `manager`, `handler`, `utils`, `helper`, `processor`.

```python
# BAD
class Contract:
    def __init__(self, amount, hourly_rate):
        self.amount = amount  # amount of what?

# GOOD
class Contract:
    def __init__(self, hours_worked: int, hourly_rate: int):
        self.hours_worked = hours_worked
```

**Detection:** If you need a comment to explain what a variable is, the name is too vague.

### 1.3 Built-in Name Shadowing

Overriding Python built-in names, causing subtle bugs.

```python
# BAD
list = [1, 2, 3]       # shadows built-in list()
id = generate_id()      # shadows built-in id()
type = "premium"         # shadows built-in type()

# GOOD
items = [1, 2, 3]
entity_id = generate_id()
account_type = "premium"
```

**Detection:** Variable or parameter names that match Python built-ins (`list`, `dict`, `id`, `type`, `input`, `map`, `filter`, `set`, `str`, `int`).

### 1.4 Asymmetric Naming

Similar classes or functions using inconsistent names for the same kind of operation.

```python
# BAD
class PowerDrill:
    def compute_rent(self, days: int) -> int: ...

class CementMixer:
    def compute_rental_price(self, from_date, to_date) -> int: ...  # different name, different signature

# GOOD — consistent naming and signatures
class PowerDrill:
    def compute_rent(self, days: int) -> int: ...

class CementMixer:
    def compute_rent(self, days: int) -> int: ...
```

**Detection:** Different names or signatures doing similar things across related classes. Missing `__str__` or `__repr__` dunder methods where custom string conversion exists.

---

## 2. Structural Smells

### 2.1 Too Many Arguments

Functions taking more than 3-4 parameters, often because related data hasn't been grouped.

```python
# BAD
def reserve_room(self, room_number, first_name, last_name, email, from_date, to_date, price): ...

# GOOD — group related data into objects
def reserve_room(self, room_id: str, customer_id: str): ...
```

**Detection:** Function signatures with 4+ parameters, especially related ones (first_name + last_name + email = Customer).

### 2.2 Too Many Instance Variables

A class with 7+ instance variables likely holds multiple responsibilities.

```python
# BAD
@dataclass
class Player:
    name: str
    strength: int
    constitution: int
    dexterity: int
    intelligence: int
    wisdom: int
    charisma: int
    health: int
    xp: int
    inventory: list

# GOOD — extract cohesive groups
@dataclass
class CharacterTraits:
    strength: int = 0
    constitution: int = 0
    dexterity: int = 0
    intelligence: int = 0
    wisdom: int = 0
    charisma: int = 0

@dataclass
class Player:
    name: str
    traits: CharacterTraits = field(default_factory=CharacterTraits)
    health: int = 100
    xp: int = 0
    inventory: list = field(default_factory=list)
```

**Detection:** Count instance variables. Prefixed fields (`customer_name`, `customer_email`) signal a missing class.

### 2.3 Redundant Instance Variables

Instance variables that can be computed from other instance variables.

```python
# BAD — total_balance duplicates information
class BankAccount:
    def __init__(self):
        self.checking_balance = 0
        self.savings_balance = 0
        self.total_balance = 0  # must be updated everywhere

# GOOD — compute derived values with properties
class BankAccount:
    def __init__(self):
        self.checking_balance = 0
        self.savings_balance = 0

    @property
    def total_balance(self) -> int:
        return self.checking_balance + self.savings_balance
```

**Detection:** Instance variables updated in multiple places alongside other variables.

### 2.4 Parallel Data Structures

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

**Detection:** Parallel lists indexed by the same variable. Zip operations joining related data.

### 2.5 Wrong Data Structure

Using a data structure that makes primary operations inefficient.

```python
# BAD — O(n) lookup every time
class VehicleRegistry:
    def __init__(self):
        self.models: list[VehicleModelInfo] = []

    def find_model(self, brand: str, model: str):
        for m in self.models:
            if m.brand == brand and m.model == model:
                return m

# GOOD — O(1) lookup
class VehicleRegistry:
    def __init__(self):
        self.models: dict[tuple[str, str], VehicleModelInfo] = {}

    def find_model(self, brand: str, model: str):
        return self.models.get((brand, model))
```

**Detection:** Linear scans through lists for lookups. Frequent sorting operations.

---

## 3. Behavioral Smells

### 3.1 Boolean Flags as Parameters

Boolean parameters that switch function behavior indicate the method does two things.

```python
# BAD
class Wallet:
    def place_order(self, amount: int, is_buying: bool):
        if is_buying:
            self.balance += amount
        else:
            self.balance -= amount

# GOOD — separate functions with clear intent
class Wallet:
    def buy(self, amount: int) -> None:
        self.balance += amount

    def sell(self, amount: int) -> None:
        self.balance -= amount
```

**Detection:** Boolean parameters that control which branch of an if/else executes.

### 3.2 Deep Nesting

More than 2-3 levels of indentation. Use guard clauses and extract functions.

```python
# BAD
def process(order):
    if order:
        if order.items:
            for item in order.items:
                if item.price > 0:
                    # actual logic buried 4 levels deep

# GOOD — guard clauses + extraction
def process(order):
    if not order or not order.items:
        return
    for item in order.items:
        process_item(item)
```

**Detection:** More than 2 levels of indentation. Nested if/for/while combinations.

### 3.3 Tell, Don't Ask Violations

Interrogating an object's state externally then acting on it, instead of telling the object to act.

```python
# BAD (ask, then act)
def normalize_vector(vector):
    length = (vector.x**2 + vector.y**2)**0.5
    vector.x = vector.x / length
    vector.y = vector.y / length

# GOOD (tell)
class Vector:
    def normalize(self) -> None:
        length = (self.x**2 + self.y**2)**0.5
        self.x /= length
        self.y /= length

vector.normalize()
```

**Detection:** Functions accessing multiple attributes of a single object to compute/modify.

### 3.4 Methods That Don't Use Self

Instance methods that never reference `self` should be static methods or module functions.

```python
# BAD
class Hotel:
    def generate_room_id(self) -> str:  # self never used
        return str(uuid.uuid4())

# GOOD
def generate_room_id() -> str:
    return str(uuid.uuid4())
```

**Detection:** Methods with `self` parameter that never reference `self`.

### 3.5 Redefining Core Concepts

Overriding `__new__`, abusing inheritance, or confusing construction patterns.

```python
# BAD — __new__ returns a different type
class Payment:
    def __new__(cls, payment_type):
        if payment_type == "card":
            return StripePayment()
        elif payment_type == "paypal":
            return PayPalPayment()

# GOOD — factory function
def create_payment(method: PaymentMethod) -> Payment:
    return {"card": StripePayment, "paypal": PayPalPayment}[method]()
```

**Detection:** Overriding `__new__` to return different types. Subclasses that break Liskov substitution.

### 3.6 Missing Function Composition

Sequential variable reassignment that could be a composed pipeline.

```python
# BAD — sequential mutation
x = 3
x = x + 3
x = x * 2
x = x + 3
x = x * 2

# GOOD — composed functions
from functools import reduce

def compose(*fns):
    return reduce(lambda f, g: lambda x: f(g(x)), fns)

add_three = lambda x: x + 3
double = lambda x: x * 2
transform = compose(double, add_three, double, add_three)
result = transform(3)
```

**Detection:** Same variable reassigned 3+ times in sequence.

---

## 4. Import & Module Smells

### 4.1 Wildcard Imports

`from module import *` destroys traceability and can cause name collisions.

```python
# BAD
from random import *
from string import *
result = ''.join(choices(ascii_uppercase, k=10))  # where is choices from?

# GOOD
import random
import string
result = ''.join(random.choices(string.ascii_uppercase, k=10))
```

### 4.2 Hardwired Dependencies

Objects create their own dependencies, making testing impossible.

```python
# BAD — hardwired
class PointOfSaleSystem:
    def __init__(self):
        self.processor = StripePaymentProcessor()

# GOOD — injected
class PointOfSaleSystem:
    def __init__(self, processor: PaymentProcessor):
        self.processor = processor
```

**Detection:** `self.x = ConcreteClass()` inside `__init__`. Impossible to substitute for testing.

### 4.3 Hardwired Initialization Sequences

Complex setup sequences the caller must remember.

```python
# BAD — forget connect_to_service and the system crashes
processor = StripePaymentProcessor()
processor.connect_to_service("https://api.stripe.com")

# GOOD — factory method guarantees proper setup
processor = StripePaymentProcessor.create(url="https://api.stripe.com")
```

**Detection:** Required method calls after construction. Documentation that says "you must call X before using Y."

---

## 5. Smell-to-Fix Quick Reference

| Smell | Category | Fix | Related Rule |
|-------|----------|-----|-------------|
| Type Abuse | Naming | Use `Enum` | Rule 1 |
| Vague Identifiers | Naming | Rename descriptively | Rule 2 |
| Built-in Shadowing | Naming | Prefix with domain term | — |
| Asymmetric Naming | Naming | Standardize + use dunders | Rule 20 |
| Too Many Arguments | Structural | Extract data object | — |
| Too Many Instance Vars | Structural | Extract sub-objects | Rule 19 |
| Redundant Variables | Structural | Use `@property` | — |
| Parallel Data Structures | Structural | Create composite type | Rule 6 |
| Wrong Data Structure | Structural | Match access pattern | — |
| Boolean Flags | Behavioral | Split into separate functions | Rule 3 |
| Deep Nesting | Behavioral | Guard clauses + extract | Rule 4 |
| Tell, Don't Ask | Behavioral | Move logic into object | Rule 5 |
| No Self Usage | Behavioral | `@staticmethod` or module function | — |
| Redefining Concepts | Behavioral | Factory function + Protocol | — |
| Missing Composition | Behavioral | Compose functions | — |
| Wildcard Imports | Import | Explicit imports | Rule 15 |
| Hardwired Dependencies | Import | Dependency injection | — |
| Hardwired Init Sequences | Import | Factory method or `__init__` | Rule 22 |

*Rule numbers reference `code-quality.md`.*

---

## 6. Code Review Checklist (Smell Edition)

When scanning code for smells, check in this order:

1. **Naming** — Any `data`, `info`, `manager`, `handler`, `utils`? Any string-compared constants?
2. **Signatures** — Any function with 4+ params? Any boolean flags?
3. **Classes** — Any class with 7+ instance vars? Any redundant stored state? Any method that doesn't use `self`?
4. **Nesting** — Any block indented 3+ levels?
5. **Imports** — Any wildcard imports? Any circular dependencies?
6. **Construction** — Any `self.x = ConcreteClass()` in `__init__`? Any required setup methods?
7. **Symmetry** — Do related classes use consistent naming and signatures?

> Content inspired by Arjan Codes' *Software Designer Mindset* (Design Wins) and code smell analysis videos.
