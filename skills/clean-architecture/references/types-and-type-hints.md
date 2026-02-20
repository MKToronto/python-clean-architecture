# Types and Type Hints Reference

Type hints are a developer tool that improves readability, catches errors early, and establishes contracts between components. Python's interpreter ignores them entirely at runtime, but static analysis tools and IDEs use them to surface bugs before the code ever executes. Content inspired by Arjan Codes' Software Designer Mindset course.

## 1. Python's Type System

Python sits at a specific intersection of two independent axes: **static vs dynamic** typing and **strong vs weak** typing. Understanding where Python lands on each axis explains why type hints exist and what they can (and cannot) do.

### Static vs Dynamic Typing

This axis determines **when** type information is checked.

- **Static typing** (Java, C#, Go): Types are checked at compile time. A variable declared as `int` can never hold a string. The compiler rejects the program before it runs.
- **Dynamic typing** (Python, Ruby): Types are checked at runtime. Variables do not have types -- values do. A variable can refer to a string on one line and an integer on the next.

```python
# Python is dynamically typed: variables don't have types, values do.
my_var = "hello"
print(my_var)  # hello

my_var = 5
print(my_var)  # 5 -- same variable, different type of value
```

In Java, this reassignment would be a compile-time error. In Python, it runs without complaint because the variable is simply a name pointing to a value, and values carry their own type.

### Strong vs Weak Typing

This axis determines **how strictly** types are enforced when operations combine different types.

- **Strong typing** (Python, Java): No implicit type conversions. Attempting to add `5 + "hello"` raises a `TypeError`.
- **Weak typing** (JavaScript, PHP): The language silently converts types to make operations succeed. `5 + "hello"` produces `"5hello"` in JavaScript.

```python
# Python is strongly typed: no implicit conversions.
result = 5 + "hello"
# TypeError: unsupported operand type(s) for +: 'int' and 'str'

# Explicit conversion is required.
result = str(5) + "hello"  # "5hello"
```

Strong typing forces deliberate type conversions, which prevents an entire category of silent bugs where the language "helpfully" converts values in unexpected ways.

### Python's Position: Dynamic + Strong

Python checks types at runtime (dynamic) and refuses to silently convert between incompatible types (strong). This combination means:

- Flexibility to reassign variables to different types
- Runtime `TypeError` exceptions when incompatible types interact
- Type errors surface as exceptions integrated into Python's error handling, not as compiler messages

| Language   | Static/Dynamic | Strong/Weak |
|------------|----------------|-------------|
| Java, C#   | Static         | Strong      |
| Python     | Dynamic        | Strong      |
| JavaScript | Dynamic        | Weak        |
| C          | Static         | Weak        |

---

## 2. Why Use Type Hints

Type hints are **purely informational**. The Python interpreter skips them completely during execution. A function annotated with the wrong types still runs if the actual values support the operations performed on them.

```python
def add3(x: str) -> str:
    return x + 3

# The type hints say str, but the call passes an int.
print(add3(5))  # Prints 8 -- Python ignores the hints at runtime.
```

Despite being optional, type hints deliver four concrete benefits:

### Documentation

Without type hints, the only way to know what a function expects is to read its implementation or hope for a docstring.

```python
# What are users, plants, and products?
# Lists? Sets? Integers? IDs? There is no way to tell.
def compute_stats(users, plants, products):
    ...
```

```python
# Now the function signature is self-documenting.
def compute_stats(
    users: list[str],
    plants: list[str],
    products: list[str],
) -> dict[str, float]:
    ...
```

### IDE Support

Type hints unlock autocomplete, inline documentation, and go-to-definition in editors like VS Code (via Pylance/Pyright) and PyCharm. The IDE knows the return type and offers accurate suggestions on the result.

### Static Analysis

Tools like mypy and Pyright catch type errors before the program runs. This is especially valuable in large codebases where a runtime `TypeError` might not surface until a rarely-executed code path is triggered in production.

### Contracts Between Components

Type hints establish an explicit agreement between the caller and the function. The function declares what it needs and what it returns. The caller knows exactly what to provide. When either side changes, the type checker flags the mismatch immediately.

---

## 3. Basic Type Hints

Annotate function parameters with `: type` and return values with `-> type`. Always specify both.

### Primitive Types

```python
def add3(x: int) -> int:
    return x + 3


def greet(name: str) -> str:
    return f"Hello, {name}"


def is_adult(age: int) -> bool:
    return age >= 18


def compute_tax(price: float, tax_rate: float) -> float:
    return price * tax_rate
```

### Collection Types

Python 3.9+ supports built-in collection types directly in annotations. For earlier versions, import from `typing`.

```python
# Python 3.9+
def average(values: list[float]) -> float:
    return sum(values) / len(values)


def unique_names(names: list[str]) -> set[str]:
    return set(names)


def word_count(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for word in text.split():
        counts[word] = counts.get(word, 0) + 1
    return counts
```

### Optional and Union Types

```python
from typing import Optional

# A value that might be None
def find_user(user_id: int) -> Optional[str]:
    users = {1: "Alice", 2: "Bob"}
    return users.get(user_id)


# Python 3.10+ union syntax
def parse_input(value: str) -> int | float:
    if "." in value:
        return float(value)
    return int(value)
```

### None Return Type

Functions that perform an action but return nothing use `-> None`:

```python
def log_message(message: str) -> None:
    print(f"[LOG] {message}")
```

### Typed vs Untyped -- Side by Side

```python
# WITHOUT type hints: what does this function expect? What does it return?
def process_order(order, discount, tax):
    subtotal = order["price"] * order["quantity"]
    discounted = subtotal * (1 - discount)
    return discounted * (1 + tax)


# WITH type hints: the signature is self-documenting.
def process_order(order: dict[str, float], discount: float, tax: float) -> float:
    subtotal = order["price"] * order["quantity"]
    discounted = subtotal * (1 - discount)
    return discounted * (1 + tax)
```

---

## 4. Callable Types

In Python, functions are objects. A variable can hold a reference to a function, and that variable's type is `Callable`. Import it from `typing` and specify the argument types and return type.

### Basic Callable Syntax

`Callable[[ArgType1, ArgType2], ReturnType]` -- the first element is a list of argument types, the second is the return type.

```python
from typing import Callable


def add3(x: int) -> int:
    return x + 3


# my_func holds a reference to a function, not to a return value.
my_func: Callable[[int], int] = add3
print(my_func(5))  # 8
```

### Type Aliases for Readability

Complex `Callable` signatures become unreadable fast. Define a type alias to give the callable a meaningful name.

```python
from typing import Callable


# Type alias: a function that takes an int and returns an int.
IntTransform = Callable[[int], int]


def add3(x: int) -> int:
    return x + 3


def double(x: int) -> int:
    return x * 2


def apply_transform(value: int, transform: IntTransform) -> int:
    return transform(value)


print(apply_transform(5, add3))    # 8
print(apply_transform(5, double))  # 10
```

### Type Safety with Callables

Callable types catch mismatches between expected and actual function signatures.

```python
from typing import Callable

IntFunction = Callable[[int], int]


def add3(x: int) -> int:
    return x + 3


def multiply_by_two(x: float) -> float:
    return x * 2.0


my_func: IntFunction = add3            # OK: signatures match
my_func: IntFunction = multiply_by_two  # Type error: expects int, got float
```

The type checker flags `multiply_by_two` because its parameter and return types are `float`, not `int`. The program still runs (Python ignores hints at runtime), but the static analysis tool reports the mismatch.

### Practical Example: Discount Strategies

```python
from typing import Callable
from dataclasses import dataclass

DiscountFunction = Callable[[int], int]


@dataclass
class Order:
    item: str
    price: int


def no_discount(price: int) -> int:
    return price


def ten_percent_off(price: int) -> int:
    return int(price * 0.9)


def holiday_discount(price: int) -> int:
    return int(price * 0.75)


def apply_discount(order: Order, discount: DiscountFunction) -> int:
    return discount(order.price)


order = Order(item="Laptop", price=1000)
print(apply_discount(order, no_discount))       # 1000
print(apply_discount(order, ten_percent_off))    # 900
print(apply_discount(order, holiday_discount))   # 750
```

The `DiscountFunction` alias makes the function signature readable. Any function matching `Callable[[int], int]` can serve as a discount strategy.

---

## 5. Nominal vs Structural Typing

Python supports two fundamentally different approaches to determining whether an object satisfies a type requirement.

### Nominal Typing

Nominal typing determines type compatibility based on **class name and inheritance hierarchy**. An object is of type `Animal` only if its class explicitly inherits from `Animal`.

```python
from abc import ABC, abstractmethod


class Animal(ABC):
    @abstractmethod
    def speak(self) -> str:
        ...


class Dog(Animal):
    def speak(self) -> str:
        return "Woof"


class Cat(Animal):
    def speak(self) -> str:
        return "Meow"


# Robot has a speak() method but does NOT inherit from Animal.
class Robot:
    def speak(self) -> str:
        return "Beep"


def make_sound(animal: Animal) -> str:
    return animal.speak()


make_sound(Dog())    # OK: Dog inherits from Animal
make_sound(Cat())    # OK: Cat inherits from Animal
make_sound(Robot())  # Type error: Robot is not an Animal (nominal mismatch)
```

With nominal typing, `Robot` fails the type check even though it has the exact same `speak()` method. The name and hierarchy matter, not the shape.

### Structural Typing (Duck Typing)

Structural typing determines type compatibility based on **what an object can do**, not what it inherits from. This is Python's natural mode: "if it walks like a duck and quacks like a duck, then it must be a duck."

Python's built-in `len()` function demonstrates structural typing. It works on strings, lists, dicts, and any custom class that defines `__len__`:

```python
class Book:
    def __init__(self, author: str, title: str, pages: int) -> None:
        self.author = author
        self.title = title
        self.pages = pages

    def __len__(self) -> int:
        return self.pages


# len() works on anything with a __len__ method.
print(len("hello"))                                    # 5
print(len([1, 2, 3]))                                  # 3
print(len({"a": 1, "b": 2}))                           # 2
print(len(Book("Robert Martin", "Clean Code", 464)))    # 464
```

`Book` has no inheritance relationship with `str`, `list`, or `dict`. But `len()` works on all of them because they share the same **structure**: a `__len__` method.

### Protocol: Formalizing Structural Typing

The `Protocol` class (from `typing`) bridges duck typing and static analysis. Define the methods an object must have, without requiring inheritance.

```python
from typing import Protocol


class Speaker(Protocol):
    def speak(self) -> str:
        ...


class Dog:
    def speak(self) -> str:
        return "Woof"


class Cat:
    def speak(self) -> str:
        return "Meow"


class Robot:
    def speak(self) -> str:
        return "Beep"


def make_sound(speaker: Speaker) -> str:
    return speaker.speak()


# All three work -- no inheritance required.
# The type checker verifies each class has a speak() -> str method.
make_sound(Dog())    # "Woof"
make_sound(Cat())    # "Meow"
make_sound(Robot())  # "Beep"
```

`Dog`, `Cat`, and `Robot` never reference `Speaker`. They satisfy the protocol purely by having a `speak()` method that returns `str`. The type checker verifies the structural match.

### Protocol vs ABC -- When to Use Each

| Aspect | ABC (Nominal) | Protocol (Structural) |
|--------|---------------|----------------------|
| Coupling | Classes must explicitly inherit from the ABC | Classes have zero knowledge of the Protocol |
| Flexibility | Only subclasses pass the type check | Any class with matching methods passes |
| Enforcement | `@abstractmethod` prevents instantiation of incomplete subclasses | Type checker flags missing methods, but runtime does not enforce |
| Python idiom | More Java/C# style | More Pythonic (duck typing) |
| Best for | Framework extension points where you control the hierarchy | Interfaces between decoupled components |

Prefer `Protocol` for defining interfaces in clean architecture. It keeps components decoupled because the implementing class never imports or references the protocol definition.

---

## 6. Trade-offs

Type hints are not free. Three trade-offs deserve explicit consideration.

### Trade-off 1: Cryptic Error Messages

Complex type definitions produce error messages that are difficult to parse. A deeply nested generic type like `dict[str, list[tuple[int, Callable[[str], Optional[float]]]]]` generates error output that obscures the actual problem.

```python
# Simple types produce clear errors.
def add(x: int, y: int) -> int:
    return x + y

add("hello", 5)
# Error: Argument 1 to "add" has incompatible type "str"; expected "int"


# Complex types produce cryptic errors.
from typing import Callable, Optional

Registry = dict[str, list[tuple[int, Callable[[str], Optional[float]]]]]

def process(registry: Registry) -> None:
    ...

# The error message for a type mismatch here becomes nearly unreadable.
```

Mitigate this by breaking complex types into named aliases and keeping nesting shallow.

### Trade-off 2: Overly Specific Types Restrict Functionality

Choosing a type that is too narrow prevents valid use cases. Use the **broadest appropriate type** that still communicates intent.

```python
# TOO SPECIFIC: only accepts int, excludes float.
def compute_pay(hours: int, rate: int) -> int:
    return hours * rate

compute_pay(37.5, 25.50)  # Type error -- but this is a valid use case.


# BETTER: use float to accept both int and float values.
def compute_pay(hours: float, rate: float) -> float:
    return hours * rate

compute_pay(40, 25)       # Works (int is compatible with float)
compute_pay(37.5, 25.50)  # Works
```

The same principle applies to collections. Accept `Iterable[T]` instead of `list[T]` when the function only needs to iterate:

```python
from typing import Iterable


# RESTRICTIVE: only accepts list
def total_prices(prices: list[float]) -> float:
    return sum(prices)


# FLEXIBLE: accepts list, tuple, set, generator, or any iterable
def total_prices(prices: Iterable[float]) -> float:
    return sum(prices)
```

### Trade-off 3: Third-Party Libraries Often Lack Type Hints

Many Python packages do not include type annotations. Running a strict type checker against code that uses these packages produces a flood of warnings about unknown types, which drowns out genuine errors in your own code.

Strategies to manage this:

- Use `# type: ignore` comments sparingly on specific lines involving untyped libraries
- Install type stubs when available (e.g., `types-requests`, `boto3-stubs`)
- Configure the type checker to treat untyped imports as `Any` rather than errors
- Focus strict type checking on your own code, not third-party integrations

---

## 7. Best Practices

### Annotate Every Function

Type hint every function parameter and every return value. This applies to public APIs, private helpers, and module-level functions. The signature becomes self-documenting, and the type checker can trace errors across call boundaries.

```python
# Every parameter and the return value are annotated.
def create_invoice(
    customer_id: str,
    items: list[dict[str, float]],
    tax_rate: float,
) -> dict[str, float]:
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    tax = subtotal * tax_rate
    return {"subtotal": subtotal, "tax": tax, "total": subtotal + tax}
```

### Prefer Structural Typing (Protocols)

Use `Protocol` to define interfaces instead of abstract base classes. This keeps components decoupled and follows Python's duck typing philosophy.

```python
from typing import Protocol


class Repository(Protocol):
    def save(self, entity: dict) -> None: ...
    def find_by_id(self, entity_id: str) -> dict | None: ...


class PostgresRepository:
    """Satisfies Repository protocol without importing or inheriting it."""

    def save(self, entity: dict) -> None:
        print(f"Saving to Postgres: {entity}")

    def find_by_id(self, entity_id: str) -> dict | None:
        print(f"Querying Postgres for: {entity_id}")
        return None


class InMemoryRepository:
    """Test double -- also satisfies Repository protocol."""

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def save(self, entity: dict) -> None:
        self._store[entity["id"]] = entity

    def find_by_id(self, entity_id: str) -> dict | None:
        return self._store.get(entity_id)


def process_order(order: dict, repo: Repository) -> None:
    repo.save(order)
```

Both `PostgresRepository` and `InMemoryRepository` satisfy the `Repository` protocol without ever importing it. Swap implementations freely in production code and tests.

### Keep Type Definitions Readable

Break complex types into named aliases. Each alias should have a clear, domain-relevant name.

```python
from typing import Callable

# BAD: inline complex type
def apply(
    value: int,
    transforms: list[Callable[[int], int]],
    validator: Callable[[int], bool],
) -> int:
    ...


# GOOD: named aliases
IntTransform = Callable[[int], int]
IntValidator = Callable[[int], bool]

def apply(
    value: int,
    transforms: list[IntTransform],
    validator: IntValidator,
) -> int:
    ...
```

### Use Static Analysis Tools

Integrate a type checker into the development workflow. Run it on every save or as part of CI.

- **mypy**: The original Python type checker. Mature, widely supported, configurable strictness levels.
- **Pyright / Pylance**: Fast type checker from Microsoft. Pylance is the VS Code extension built on Pyright. Catches errors in real time as you type.

```bash
# Run mypy on a module
mypy src/

# Run pyright on a module
pyright src/
```

Configure strict mode to maximize coverage:

```ini
# mypy.ini
[mypy]
strict = True
warn_return_any = True
warn_unused_configs = True
```

### Use the Broadest Appropriate Type

Accept the most general type that supports the operations the function performs. This maximizes the function's reusability without sacrificing type safety.

| Function needs to... | Use |
|---|---|
| Iterate over items | `Iterable[T]` |
| Access items by index | `Sequence[T]` |
| Mutate items in place | `list[T]` |
| Look up by key | `Mapping[K, V]` |
| Accept any callable | `Callable[[...], ReturnType]` |
