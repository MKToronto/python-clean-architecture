# Function Design Reference

Functions are the core building block of clean Python architecture. Master them before reaching for classes. Content inspired by Arjan Codes' Software Designer Mindset course.

## 1. Functions as First-Class Objects

In Python, everything is an object -- including functions. Every function has a type (`function`), attributes, and a `__call__` method. This means you can assign functions to variables, store them in data structures, and pass them as arguments.

### The `__call__` Method

Any object with a `__call__` method is callable. A `def` statement creates an object whose `__call__` executes the function body.

```python
class PriceCalculator:
    def __init__(self, tax_rate: float) -> None:
        self.tax_rate = tax_rate

    def __call__(self, base_price: float) -> float:
        return base_price * (1 + self.tax_rate)


# Use it like a function
calculate_price = PriceCalculator(tax_rate=0.21)
total = calculate_price(100.0)  # 121.0
```

### Everything Is an Object

Functions, integers, strings -- they all have a `__class__` attribute. Verify this yourself:

```python
def greet(name: str) -> str:
    return f"Hello, {name}"


print(type(greet))          # <class 'function'>
print(type(42))             # <class 'int'>
print(greet.__call__("Alice"))  # "Hello, Alice" — same as greet("Alice")
```

### Passing Functions Around

Because functions are objects, store them in lists, dicts, or pass them as arguments:

```python
def add(x: int, y: int) -> int:
    return x + y

def multiply(x: int, y: int) -> int:
    return x * y


operations: dict[str, Callable[..., int]] = {
    "add": add,
    "multiply": multiply,
}

result = operations["add"](3, 4)  # 7
```

---

## 2. Value Constraints and Fail-Fast

Validate function inputs at the boundary — fail immediately with a clear error rather than propagating bad data deep into the system.

```python
# BAD: silently produces wrong result with negative price
def compute_total(price: float, quantity: int) -> float:
    return price * quantity

# GOOD: fail fast on invalid input
def compute_total(price: float, quantity: int) -> float:
    if price < 0:
        raise ValueError(f"Price must be non-negative, got {price}")
    if quantity < 0:
        raise ValueError(f"Quantity must be non-negative, got {quantity}")
    return price * quantity
```

**Where to validate:** At system boundaries — function entry points, API endpoints, constructors. Internal helper functions called only by already-validated code can trust their inputs.

**Return value conventions:** Prefer raising exceptions for errors over returning `None` or sentinel values. A function that returns `Optional[X]` forces every caller to check for `None`. A function that raises makes the happy path clean and the error path explicit.

```python
# AVOID: caller must check for None
def find_user(user_id: str) -> User | None:
    ...

# PREFER: caller gets a User or an exception
def find_user(user_id: str) -> User:
    user = db.get(user_id)
    if user is None:
        raise NotFoundError(f"User not found: {user_id}")
    return user
```

---

## 3. Pure Functions

A pure function produces the same output for the same inputs every time. It reads nothing from the outside world and changes nothing in it.

### Characteristics

- Depends only on its input arguments
- Returns a result without modifying external state
- Does not use random numbers, current time, or file I/O
- Trivial to test: call with arguments, assert on return value

```python
# PURE: depends only on inputs, always returns the same result
def compute_total(price: float, quantity: int, tax_rate: float) -> float:
    return price * quantity * (1 + tax_rate)


# NOT PURE: depends on current time
from datetime import datetime

def is_business_hours() -> bool:
    return 9 <= datetime.now().hour < 17
```

### Why Pure Functions Matter

- **Testability**: No setup required. Pass arguments, check the return value.
- **Predictability**: No hidden dependencies or state changes to track.
- **Composability**: Safe to combine, reorder, or run in parallel.
- **Debugging**: If the output is wrong, the inputs tell the whole story.

```python
# Testing a pure function requires zero setup
def test_compute_total():
    assert compute_total(price=10.0, quantity=3, tax_rate=0.2) == 36.0
```

---

## 4. Side Effects

A side effect is any observable change a function makes outside its own scope: modifying a global variable, writing to a file, mutating an argument, printing to the console.

### Recognizing Side Effects

```python
customers = {"alice": {"phone": "555-0001"}}

# SIDE EFFECT: modifies a global dictionary
def update_phone_bad() -> None:
    customers["alice"]["phone"] = "555-9999"

# SIDE EFFECT: mutates an argument in place
def update_phone_still_bad(data: dict) -> None:
    data["alice"]["phone"] = "555-9999"
```

### Eliminating Side Effects with Dependency Injection

Instead of reaching into global state, accept dependencies as arguments. Instead of mutating data, return new data.

```python
from dataclasses import dataclass


@dataclass
class Customer:
    name: str
    phone: str


# PURE: accepts input, returns new value, mutates nothing
def update_customer_phone(customer: Customer, new_phone: str) -> Customer:
    return Customer(name=customer.name, phone=new_phone)


# Usage
alice = Customer(name="Alice", phone="555-0001")
alice_updated = update_customer_phone(alice, "555-9999")
```

### When Side Effects Are Unavoidable

Some functions must interact with the outside world (database writes, HTTP calls, file I/O). Isolate these at the edges of the system:

```python
from typing import Protocol


class CustomerRepository(Protocol):
    def save(self, customer: Customer) -> None: ...


# Pure business logic — no side effects
def apply_discount(customer: Customer, discount: float) -> Customer:
    return Customer(name=customer.name, phone=customer.phone)


# Side effects isolated at the boundary
def process_discount(
    customer: Customer,
    discount: float,
    repo: CustomerRepository,
) -> None:
    updated = apply_discount(customer, discount)
    repo.save(updated)  # side effect pushed to the edge
```

---

## 5. Higher-Order Functions

A higher-order function either accepts a function as an argument or returns a function as its result. This is the mechanism behind strategy injection, callback patterns, and decorators.

### Accepting a Function as an Argument

Separate the "what to do" from the "decision logic" by passing the decision as a callable:

```python
from dataclasses import dataclass
from typing import Callable


@dataclass
class Customer:
    name: str
    age: int


def send_email_promotion(
    customers: list[Customer],
    is_eligible: Callable[[Customer], bool],
) -> None:
    for customer in customers:
        if is_eligible(customer):
            print(f"Sending promotion to {customer.name}")
        else:
            print(f"Skipping {customer.name}")


# Define different eligibility strategies
def is_senior(customer: Customer) -> bool:
    return customer.age >= 50


def is_adult(customer: Customer) -> bool:
    return customer.age >= 18


# Swap behavior without changing send_email_promotion
customers = [
    Customer("Alice", 25),
    Customer("Bob", 35),
    Customer("Charlie", 55),
]

send_email_promotion(customers, is_eligible=is_senior)
# Sending promotion to Charlie only

send_email_promotion(customers, is_eligible=is_adult)
# Sending promotion to Alice, Bob, and Charlie
```

### Returning a Function

A function can build and return another function. This is the basis for closures and factory functions:

```python
def make_multiplier(factor: int) -> Callable[[int], int]:
    def multiplier(x: int) -> int:
        return x * factor
    return multiplier


double = make_multiplier(2)
triple = make_multiplier(3)

print(double(5))   # 10
print(triple(5))   # 15
```

### Grouping Functions in Data Structures

Use lists, tuples, or dicts to group related callables and iterate over them:

```python
from typing import Callable, Iterable


PostProcessor = Callable[[float], None]


def log_payment(amount: float) -> None:
    print(f"Logged payment of ${amount:.2f}")


def send_receipt(amount: float) -> None:
    print(f"Sent receipt for ${amount:.2f}")


def apply_loyalty_points(amount: float) -> None:
    points = int(amount // 10)
    print(f"Awarded {points} loyalty points")


def handle_post_processors(
    amount: float,
    processors: Iterable[PostProcessor],
) -> None:
    for process in processors:
        process(amount)


# Group functions using a tuple (immutable = safe to pass around)
post_processors: tuple[PostProcessor, ...] = (
    log_payment,
    send_receipt,
    apply_loyalty_points,
)

handle_post_processors(150.0, post_processors)
```

Use `Iterable` as the parameter type. This accepts lists, tuples, sets, or generators -- and guarantees the function will not mutate the collection.

---

## 6. Closures

A closure is a nested function that captures variables from its enclosing scope. Use closures to separate configuration-time arguments from call-time arguments.

### The Problem: Mismatched Signatures

When a higher-order function expects `Callable[[Customer], bool]` but your logic needs an extra parameter:

```python
# send_email_promotion expects: Callable[[Customer], bool]
# But we need a cutoff_age parameter -- where does it go?

def is_eligible_for_promotion(customer: Customer, cutoff_age: int) -> bool:
    return customer.age >= cutoff_age
```

### The Closure Solution

Wrap the inner function inside an outer function that accepts the configuration:

```python
def make_age_checker(cutoff_age: int) -> Callable[[Customer], bool]:
    def is_eligible(customer: Customer) -> bool:
        return customer.age >= cutoff_age  # captures cutoff_age from outer scope
    return is_eligible


# Configure at creation time, use at call time
check_seniors = make_age_checker(50)
check_adults = make_age_checker(18)

send_email_promotion(customers, is_eligible=check_seniors)
send_email_promotion(customers, is_eligible=check_adults)
```

The inner function `is_eligible` "closes over" the `cutoff_age` variable from the enclosing `make_age_checker` scope. That value persists even after `make_age_checker` has returned.

### Real-World Closure: Database Connection Factory

```python
from typing import Callable


def make_query_executor(connection_string: str) -> Callable[[str], list[dict]]:
    # Expensive setup happens once
    connection = create_connection(connection_string)

    def execute_query(sql: str) -> list[dict]:
        # Reuses the captured connection on every call
        cursor = connection.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    return execute_query


# Configure once
run_query = make_query_executor("postgresql://localhost/mydb")

# Use many times -- connection is already established
users = run_query("SELECT * FROM users")
orders = run_query("SELECT * FROM orders")
```

---

## 7. `functools.partial`

`functools.partial` pre-fills arguments on an existing function and returns a new callable with fewer parameters. It achieves the same result as a closure but without writing nested functions.

### Basic Usage

```python
from functools import partial


def is_eligible_for_promotion(customer: Customer, cutoff_age: int) -> bool:
    return customer.age >= cutoff_age


# Create specialized versions by pre-filling cutoff_age
is_senior = partial(is_eligible_for_promotion, cutoff_age=50)
is_adult = partial(is_eligible_for_promotion, cutoff_age=18)

# Both now match Callable[[Customer], bool]
send_email_promotion(customers, is_eligible=is_senior)
send_email_promotion(customers, is_eligible=is_adult)
```

### When to Use `partial` vs Closures

| Use `partial` when... | Use a closure when... |
|---|---|
| Pre-filling arguments on an existing function | You need setup logic before returning the inner function |
| The original function already exists and has the right signature | The inner function needs to combine multiple captured variables |
| You want a one-liner without nesting | You want a descriptive outer function name for documentation |
| No extra computation is needed at creation time | Expensive initialization should happen once at creation time |

### Practical Example: Configuring Validators

```python
from functools import partial
from typing import Callable


def validate_range(value: float, min_val: float, max_val: float) -> bool:
    return min_val <= value <= max_val


# Build specific validators from a general one
validate_percentage = partial(validate_range, min_val=0.0, max_val=100.0)
validate_temperature = partial(validate_range, min_val=-273.15, max_val=1_000_000.0)

print(validate_percentage(50.0))    # True
print(validate_percentage(150.0))   # False
print(validate_temperature(-300.0)) # False
```

---

## 8. Lambda Functions

A lambda is a short, anonymous, inline callable limited to a single expression. Use lambdas when a full `def` statement would be overkill.

### Syntax

```python
# lambda arguments: expression
square = lambda x: x ** 2

# Equivalent named function
def square(x: int) -> int:
    return x ** 2
```

### Common Use Cases

Lambdas work well as throwaway callables passed to higher-order functions:

```python
customers = [
    Customer("Alice", 25),
    Customer("Bob", 35),
    Customer("Charlie", 55),
]

# Sort by age
sorted_customers = sorted(customers, key=lambda c: c.age)

# Filter with a one-off condition
send_email_promotion(customers, is_eligible=lambda c: c.age >= 30)

# Simple key extraction for max/min
oldest = max(customers, key=lambda c: c.age)
```

### Lambda with No Arguments or Multiple Arguments

```python
# No arguments
get_default = lambda: "N/A"

# Multiple arguments
add = lambda x, y: x + y
```

### Limitations

- **Single expression only.** No statements, no assignments, no multi-line logic.
- **No type annotations.** The type checker cannot verify lambda signatures as easily.
- **Hard to debug.** Stack traces show `<lambda>` instead of a meaningful name.

### When to Use Named Functions Instead

Use a named `def` when:
- The logic requires more than one expression
- The function is reused in multiple places
- A descriptive name improves readability
- Type annotations are important for the codebase

```python
# BAD: lambda is too complex, hard to read
process = lambda order: (
    order.total * 1.1 if order.is_taxable else order.total
)

# GOOD: named function is clearer
def compute_order_total(order: Order) -> float:
    if order.is_taxable:
        return order.total * 1.1
    return order.total
```

---

## 9. Function Header Design Rules

Well-designed function signatures communicate intent and prevent misuse:

- **Be specific in arguments, generic in returns.** Accept the narrowest type that works (`list[str]` not `Any`), but return the most specific type available. This makes calls type-safe and results useful.
- **Limit to 3-4 parameters.** When a function needs more, group related parameters into a dataclass or use keyword-only arguments (`*` separator).
- **Use keyword-only arguments for clarity.** Force callers to name ambiguous arguments:

```python
# BAD: what does True mean?
create_user("Alice", True, False)

# GOOD: keyword-only after *
def create_user(name: str, *, is_admin: bool = False, send_welcome: bool = True) -> User:
    ...

create_user("Alice", is_admin=True, send_welcome=False)
```

- **Default arguments must be immutable.** Never use `[]`, `{}`, or `set()` as defaults. Use `None` and create inside the body, or `field(default_factory=list)` in dataclasses. See Rule 14 in `code-quality.md`.

---

## 10. When to Use Classes vs Functions vs Modules

There is no rigid rule. Choose the mechanism that matches the structure of the problem.

### Use Classes When...

- **Data and behavior belong together.** A `Customer` with name, age, and a method to check eligibility.
- **You need properties.** Computed attributes like `order.total_price` read more naturally as properties.
- **You need structured data.** Dataclasses define shape, defaults, and let the IDE catch errors.
- **You need inheritance for abstraction.** One level deep: Protocol/ABC to concrete implementation.

```python
from dataclasses import dataclass


@dataclass
class Order:
    items: list[str]
    quantities: list[int]
    prices: list[float]

    @property
    def total_price(self) -> float:
        return sum(q * p for q, p in zip(self.quantities, self.prices))
```

### Use Functions When...

- **Behavior is stateless.** The function depends only on its arguments.
- **You need a single operation.** No grouping of related behaviors needed.
- **You want shorter, simpler code.** Functions avoid the overhead of class boilerplate.
- **You are implementing a strategy.** Pass a callable instead of a strategy class.

```python
def compute_rental_cost(days: int, km: int, rate_per_day: float) -> float:
    return days * rate_per_day + max(0, km - 100) * 0.25
```

### Use Modules When...

- **You need to group related functions without shared state.** A module is simpler than a behavior-only class.
- **Python already gives you the namespace.** `import pricing` then `pricing.compute_total()`.
- **You want to avoid unnecessary classes.** In Python, a module with functions replaces the "static class" pattern from Java.

```python
# pricing.py — a module that groups related functions
def compute_subtotal(prices: list[float], quantities: list[int]) -> float:
    return sum(p * q for p, q in zip(prices, quantities))

def apply_tax(subtotal: float, tax_rate: float) -> float:
    return subtotal * (1 + tax_rate)

def apply_discount(total: float, discount_pct: float) -> float:
    return total * (1 - discount_pct / 100)
```

### Decision Guide

| Situation | Prefer |
|---|---|
| Data with a few related operations | Class (dataclass) |
| Computed attributes (e.g., total price) | Class with `@property` |
| Stateless transformation or computation | Function |
| Swappable behavior (strategy) | Function passed as `Callable` |
| Grouping related stateless functions | Module |
| Need inheritance / polymorphism | Class with Protocol or ABC |
| Configuration-time vs call-time arguments | Closure or `functools.partial` |
| Short inline throwaway logic | Lambda |

### The General Rule

Keep classes either data-focused (mostly fields, few methods) or behavior-focused (mostly methods, few fields). If a class is behavior-focused with no meaningful state, replace it with a module of functions. Your code will be shorter, and your tests will be simpler.

### When to Convert a Single-Method Class to a Function

Pattern files show progressions from class-based to functional implementations. Use these criteria to decide when the conversion is appropriate:

**Convert to a plain function when:**
- The class has a single method and no instance state
- The class has no meaningful data — it's just wrapping a function
- The class has only `@staticmethod` methods (no `self` at all — the class is just a namespace)
- You don't need multiple instances with different configurations

**Keep as a callable class (`__call__` + dataclass) when:**
- The class stores configuration that differs between instances (e.g., `PercentageDiscount(percentage=0.15)`)
- You need named, inspectable configuration — `partial` loses parameter names in type checkers
- The callable carries mutable state between invocations (counter, cache)

**Use a closure / function builder when:**
- Configuration-time arguments differ in kind from runtime arguments
- You want to build specialized functions from a generic template
- The closure is short (1-3 lines); longer logic belongs in a class or named inner function

**Use `functools.partial` when:**
- Configuration arguments are a subset of the function's regular parameters
- You don't need type checker precision on the returned callable

**Don't convert when:**
- The functional version becomes less readable (e.g., `partial` everywhere loses clarity — a class provides context more naturally)
- The class produces complex objects, not simple return values
- A two-branch `if/else` that will never grow doesn't need a strategy pattern at all (KISS)
