# Value Objects

Wrap primitive types in domain-specific classes that validate on construction. Eliminates entire categories of bugs where bare `float`, `str`, or `int` values are passed in the wrong order, at the wrong scale, or with invalid data.

---

## The Problem: Primitive Obsession

When domain concepts like prices, discounts, and email addresses are bare primitives, the type system can't prevent misuse:

```python
def apply_discount(price: float, discount: float) -> float:
    return price * (1.0 - discount)

# Works correctly
apply_discount(100.0, 0.2)  # 80.0

# Silent bugs — nothing prevents these:
apply_discount(100.0, 20)     # -1900.0 (meant 20%, passed 20)
apply_discount(-50.0, 0.1)   # -45.0 (negative price accepted)
apply_discount(0.2, 100.0)   # wrong argument order, compiles fine
```

The caller must remember conventions (is discount a fraction or percentage?), and the compiler provides zero help.

---

## Solution 1: Subclass Built-in Types

For values that behave like numbers or strings but have domain constraints, subclass the built-in type and validate in `__new__`:

```python
from typing import Any, Self


class Price(float):
    """Non-negative price value."""

    def __new__(cls, value: Any) -> Self:
        val = float(value)
        if val < 0:
            raise ValueError("Price must be non-negative")
        return super().__new__(cls, val)


class Percentage(float):
    """Fraction between 0 and 1."""

    def __new__(cls, value: Any) -> Self:
        val = float(value)
        if not 0.0 <= val <= 1.0:
            raise ValueError("Percentage must be between 0 and 1")
        return super().__new__(cls, val)

    @classmethod
    def from_percent(cls, value: Any) -> Self:
        """Create from human-readable percentage (e.g., 20 → 0.2)."""
        return cls(float(value) / 100.0)
```

Now the function signature prevents misuse at the type level:

```python
def apply_discount(price: Price, discount: Percentage) -> Price:
    return Price(price * (1.0 - discount))

# Clear and safe
price = Price(100.0)
discount = Percentage.from_percent(20)
result = apply_discount(price, discount)  # 80.0

# All of these fail early and loudly:
Price(-50)           # ValueError: Price must be non-negative
Percentage(20)       # ValueError: Percentage must be between 0 and 1
```

**Why subclass built-in types?** The value object still works everywhere a `float` works — arithmetic, comparisons, formatting — but adds validation. No wrapper overhead.

---

## Solution 2: Frozen Dataclass

For values that carry structured data or need properties, use a frozen dataclass with `__post_init__` validation:

```python
import re
from dataclasses import dataclass

EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


@dataclass(frozen=True)
class EmailAddress:
    value: str

    def __post_init__(self) -> None:
        if not EMAIL_RE.match(self.value):
            raise ValueError(f"Invalid email address: {self.value}")

    @property
    def domain(self) -> str:
        return self.value.split("@", 1)[1]
```

```python
email = EmailAddress("hello@example.com")
print(email.domain)  # example.com

EmailAddress("not-an-email")  # ValueError
```

**Key properties:**
- `frozen=True` makes it immutable — value objects should never change after creation
- Validation runs automatically on construction via `__post_init__`
- Properties provide domain-specific accessors

---

## When to Use Each Approach

| Approach | Use when... |
|---|---|
| Subclass built-in (`float`, `str`, `int`) | Value behaves exactly like the base type but with constraints |
| Frozen dataclass | Value has multiple fields, properties, or complex validation |

---

## When to Create Value Objects

- **Money** — Price, Amount, Currency (prevents mixing dollars and cents)
- **Measurements** — Distance, Weight, Temperature (prevents unit confusion)
- **Identifiers** — UserId, OrderId, SKU (prevents passing wrong ID type)
- **Constrained strings** — EmailAddress, PhoneNumber, URL (validates format)
- **Percentages/Rates** — Discount, TaxRate, InterestRate (prevents scale confusion)

**Don't create value objects for:** values with no domain constraints, internal intermediary calculations, or cases where a plain `int`/`str` is genuinely what you mean.

---

## Relationship to Other Principles

- Fixes **Primitive Obsession** (code-quality.md rule)
- Supports **Start with the Data** (design-principles.md) — model domain concepts as types
- Works with **Pydantic models** — value objects can be fields in Pydantic `BaseModel` classes
- Supports **High Cohesion** — validation lives with the data it protects
