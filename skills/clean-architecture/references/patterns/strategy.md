# Strategy Pattern

A strategy is a higher-order function. The classic OOP version wraps that idea in classes, but Python lets the pattern shed its ceremony and become what it always was: passing a function to another function.

> Content inspired by Arjan Codes' Pythonic Patterns course.

---

## 1. Problem

An `if/elif/else` chain selects between different behavioral logic inside a method. Each branch is a separate algorithm, but they are all tangled together in one place.

```python
from dataclasses import dataclass


@dataclass
class Order:
    price: int
    quantity: int

    def compute_total(self, discount_type: str) -> int:
        if discount_type == "percentage":
            discount = int(self.price * self.quantity * 0.20)
        elif discount_type == "fixed":
            discount = 10_00
        else:
            discount = 0
        return self.price * self.quantity - discount


def main() -> None:
    order = Order(price=100_00, quantity=2)
    print(order)
    print(f"Total: ${order.compute_total('percentage') / 100:.2f}")


if __name__ == "__main__":
    main()
```

### What is wrong

| Smell | Why it hurts |
|---|---|
| `discount_type` is a raw string | No compile-time validation; typos fail silently |
| Growing `if/elif` chain | Every new discount type forces a change to `compute_total` (violates Open-Closed) |
| Magic numbers (`0.20`, `10_00`) | No way to configure the percentage or fixed amount without adding more parameters |
| Mixed responsibilities | `Order` knows both how to represent an order AND how to compute every kind of discount (low cohesion) |

---

## 2. Simplest Solution: Dict Lookup

Before reaching for classes or callables, check if the if/elif chain is just mapping keys to values. If so, a dict is all you need.

```python
from dataclasses import dataclass

DISCOUNT_RATES: dict[str, float] = {
    "percentage": 0.20,
    "fixed_ten": 10_00,
}


@dataclass
class Order:
    price: int
    quantity: int

    def compute_total(self, discount_type: str) -> int:
        discount = DISCOUNT_RATES.get(discount_type, 0)
        return self.price * self.quantity - discount


def main() -> None:
    order = Order(price=100_00, quantity=2)
    print(f"Total: ${order.compute_total('percentage') / 100:.2f}")
```

This eliminates the if/elif chain with a single dict lookup. It's readable, testable, and easy to extend — add a new key to the dict and you're done.

### When dict lookup is enough

- Each branch maps to a **value** (a number, a string, a config), not a **behavior**
- All branches have the same shape (same type of result)
- No complex logic per branch — just data selection

### When you need more

- Each branch has **different logic**, not just different values
- Branches need access to runtime state (e.g., the order price)
- You need to compose or chain strategies

If you need actual behavior selection, continue to the solutions below.

---

## 3. OOP Solution

Introduce an abstract `DiscountStrategy` class. Each branch becomes a concrete subclass. `Order` depends only on the abstraction.

### With ABC

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


class DiscountStrategy(ABC):
    @abstractmethod
    def compute(self, price: int) -> int:
        """Compute the discount for the given price."""


class PercentageDiscount(DiscountStrategy):
    def compute(self, price: int) -> int:
        return int(price * 0.20)


class FixedDiscount(DiscountStrategy):
    def compute(self, price: int) -> int:
        return 10_00


@dataclass
class Order:
    price: int
    quantity: int
    discount: DiscountStrategy

    def compute_total(self) -> int:
        discount = self.discount.compute(self.price * self.quantity)
        return self.price * self.quantity - discount


def main() -> None:
    order = Order(price=100_00, quantity=2, discount=PercentageDiscount())
    print(order)
    print(f"Total: ${order.compute_total() / 100:.2f}")
    # Output: Total: $160.00
```

`Order` no longer knows which discount type it receives. Swap `PercentageDiscount()` for `FixedDiscount()` and `Order` never changes.

### With Protocol

Replace ABC with a Protocol to drop the inheritance relationship entirely. Subclasses no longer need to inherit from anything -- they just need a matching `compute` method (duck typing).

```python
from typing import Protocol
from dataclasses import dataclass


class DiscountStrategy(Protocol):
    def compute(self, price: int) -> int: ...


class PercentageDiscount:
    def compute(self, price: int) -> int:
        return int(price * 0.20)


class FixedDiscount:
    def compute(self, price: int) -> int:
        return 10_00


@dataclass
class Order:
    price: int
    quantity: int
    discount: DiscountStrategy

    def compute_total(self) -> int:
        discount = self.discount.compute(self.price * self.quantity)
        return self.price * self.quantity - discount
```

Both ABC and Protocol achieve the same decoupling. Protocol is preferred when there is no shared implementation in the base class.

### What this solves

- **Increases cohesion** -- `Order` only represents price/quantity and delegates discount logic.
- **Reduces coupling** -- `Order` depends on the abstraction, not on `PercentageDiscount` or `FixedDiscount` directly.
- **Open for extension** -- add a new discount type without touching `Order`.

### What remains unsolved

Magic numbers (`0.20`, `10_00`) are still hardcoded inside each strategy class. Configuration comes next.

---

## 4. Pythonic Progression

### Step A: Callable type alias replaces the abstract class

Each strategy class has only one method. In Python, a class with a single method is a function waiting to get out. Define a `Callable` type alias and use `__call__` to make strategy objects callable.

```python
from typing import Callable
from dataclasses import dataclass

DiscountFunction = Callable[[int], int]


class PercentageDiscount:
    def __call__(self, price: int) -> int:
        return int(price * 0.20)


class FixedDiscount:
    def __call__(self, price: int) -> int:
        return 10_00


@dataclass
class Order:
    price: int
    quantity: int
    discount: DiscountFunction

    def compute_total(self) -> int:
        discount = self.discount(self.price * self.quantity)
        return max(0, self.price * self.quantity - discount)
```

The abstraction is now a **type** (`Callable[[int], int]`), not a class hierarchy. Any callable matching that signature works -- a class with `__call__`, a plain function, a lambda. The Protocol class and the ABC are both gone.

### Step B: Configurable callable classes (solving magic numbers)

Turn the strategy classes into dataclasses that accept their configuration at construction time.

```python
from typing import Callable
from dataclasses import dataclass

DiscountFunction = Callable[[int], int]


@dataclass
class PercentageDiscount:
    percentage: float

    def __call__(self, price: int) -> int:
        return int(price * self.percentage)


@dataclass
class FixedDiscount:
    fixed: int

    def __call__(self, price: int) -> int:
        return self.fixed


@dataclass
class Order:
    price: int
    quantity: int
    discount: DiscountFunction

    def compute_total(self) -> int:
        discount = self.discount(self.price * self.quantity)
        return max(0, self.price * self.quantity - discount)


def main() -> None:
    order = Order(price=100_00, quantity=2, discount=PercentageDiscount(0.30))
    print(f"Total: ${order.compute_total() / 100:.2f}")
    # Output: Total: $140.00 (30% discount on $200)
```

Magic numbers are gone. Configuration is injected at object creation. `Order` still sees only `DiscountFunction` and never changes.

### Step C: Plain functions

Since each strategy class is really just one function, drop the class entirely.

```python
from typing import Callable
from dataclasses import dataclass

DiscountFunction = Callable[[int], int]


def percentage_discount(price: int) -> int:
    return int(price * 0.20)


def fixed_discount(price: int) -> int:
    return 10_00


@dataclass
class Order:
    price: int
    quantity: int
    discount: DiscountFunction

    def compute_total(self) -> int:
        discount = self.discount(self.price * self.quantity)
        return max(0, self.price * self.quantity - discount)


def main() -> None:
    order = Order(price=100_00, quantity=2, discount=percentage_discount)
    print(f"Total: ${order.compute_total() / 100:.2f}")
    # Output: Total: $160.00
```

The `Order` initializer is now a **higher-order function** -- it receives another function as an argument. The strategy pattern, at its core, is exactly this.

But the magic numbers are back. The function signature is `(int) -> int`, so there is no room for a configuration parameter without breaking the type alias.

### Step D: Closures (function builder)

Wrap the strategy in a builder function that captures configuration in a closure and returns a function matching `DiscountFunction`.

```python
from typing import Callable
from dataclasses import dataclass

DiscountFunction = Callable[[int], int]


def percentage_discount(percentage: float) -> DiscountFunction:
    return lambda price: int(price * percentage)


def fixed_discount(fixed: int) -> DiscountFunction:
    return lambda price: fixed


@dataclass
class Order:
    price: int
    quantity: int
    discount: DiscountFunction

    def compute_total(self) -> int:
        discount = self.discount(self.price * self.quantity)
        return max(0, self.price * self.quantity - discount)


def main() -> None:
    order = Order(price=100_00, quantity=2, discount=percentage_discount(0.15))
    print(f"Total: ${order.compute_total() / 100:.2f}")
    # Output: Total: $170.00 (15% discount on $200)
```

`percentage_discount(0.15)` does not compute a discount -- it **builds a function** that computes a 15% discount. The returned function matches `Callable[[int], int]` exactly.

The closure approach separates **configuration-time arguments** (percentage) from **runtime arguments** (price). This is the function builder pattern -- the builder's parameters can be completely different from the returned function's parameters.

### Step E: functools.partial

When the configuration arguments and the runtime arguments belong to the same function (no need for separate builder parameters), use `functools.partial` to pre-apply some arguments.

```python
from functools import partial
from typing import Callable
from dataclasses import dataclass

DiscountFunction = Callable[[int], int]


def percentage_discount(price: int, percentage: float) -> int:
    return int(price * percentage)


def fixed_discount(price: int, fixed: int) -> int:
    return fixed


@dataclass
class Order:
    price: int
    quantity: int
    discount: DiscountFunction

    def compute_total(self) -> int:
        discount = self.discount(self.price * self.quantity)
        return max(0, self.price * self.quantity - discount)


def main() -> None:
    perc_discount = partial(percentage_discount, percentage=0.12)
    order = Order(price=100_00, quantity=2, discount=perc_discount)
    print(f"Total: ${order.compute_total() / 100:.2f}")
    # Output: Total: $176.00 (12% discount on $200)
```

`partial(percentage_discount, percentage=0.12)` returns a new callable that only needs `price`. The configuration argument has already been supplied.

---

## 5. When to Use

Recognize these signals in existing code:

- **Long `if/elif/else` chain** where each branch does a variation of the same thing (different discount calculation, different sorting algorithm, different validation rule).
- **A method with a `type` or `mode` string/enum parameter** that selects between different logic paths.
- **Growing parameter lists** -- each new variant adds parameters that only apply to that variant.
- **Duplicated logic across methods** that differ only in a small behavioral step.
- **Need to swap behavior at runtime** -- the caller decides which algorithm to use.

Confirm by asking: "Does this function do different things depending on a flag, and will there be more options in the future?" If yes, extract a strategy.

---

## 6. Trade-offs

### When each approach is appropriate

| Approach | Use when... | Avoid when... |
|---|---|---|
| **Dict lookup** | Branches map keys to values (numbers, strings, configs), not behavior | Each branch has different logic or needs runtime state |
| **ABC** | Strategies share instance variables or helper methods in the base class | The strategy is a single method with no shared state |
| **Protocol** | Third-party code must satisfy the strategy interface without modification | Shared base implementation is needed |
| **Callable type alias** | Strategy is a single function; maximum flexibility wanted | Strategy requires multiple cooperating methods |
| **Closure / function builder** | Configuration args differ in kind from runtime args; need to build specialized functions | Simple parameter pre-binding suffices |
| **`functools.partial`** | Configuration args are a subset of the function's regular parameters | Config and runtime args are conceptually different; typing precision matters |

### Practical gotchas

- **`functools.partial` and type checkers.** Pylance and mypy infer `partial[int]` for the return type, losing the full callable signature. The type checker cannot verify that the partially-applied function matches `DiscountFunction`. Accept this limitation or use a closure instead when type safety is critical.
- **Lambda readability.** A single-line lambda in a closure is fine. Multi-line logic belongs in a named inner function (`def compute_discount(price: int) -> int:`), not a lambda.
- **Callable classes still have a role.** When a strategy needs to carry mutable state between invocations (e.g., a counter, a cache), a dataclass with `__call__` is cleaner than a closure with `nonlocal` variables.
- **Do not over-extract.** A two-branch `if/else` that will never grow does not need a strategy pattern. Apply KISS -- only introduce the pattern when the branching is growing or the branches are complex.
- **Protocol vs Callable.** A `Protocol` with a single method and a `Callable` type alias are functionally equivalent in Python. Prefer the `Callable` alias for brevity. Use a `Protocol` when the method name carries important semantic meaning (e.g., `def validate(self, data: dict) -> bool`).

---

## 7. Related Patterns

- **Function Builder** -- a generalization of the closure approach (Step D). The builder function's parameters are completely independent from the returned function's parameters. Covered in the Function Builder pattern reference.
- **Abstract Factory** -- strategies that produce families of related objects. Often implemented as tuples of callables with `partial` for configuration.
- **Command** -- like strategy, replaces behavior with a callable, but focuses on storing, sequencing, and undoing operations rather than selecting algorithms.
- **Bridge** -- separates two independent dimensions of variation using `Callable` type aliases, where one dimension is passed as a strategy-like function argument.
- **Pipeline** -- chains multiple strategies in sequence using function composition (`functools.reduce`).
- **Registry** -- maps string keys to strategy functions, enabling dynamic selection from configuration files or user input.
