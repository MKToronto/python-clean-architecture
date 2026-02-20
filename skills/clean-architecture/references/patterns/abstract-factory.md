# Abstract Factory Pattern

Separate the creation of families of related objects from the code that uses them. The factory groups related creation logic so consumers never depend on concrete implementations.

> Content inspired by Arjan Codes' Pythonic Patterns course.

---

## 1. Problem

Recognize these code smells as triggers for the Abstract Factory pattern:

- **Boolean flags controlling object creation.** A function takes `use_nl_tax: bool` and `has_capital_tax: bool` to decide which calculation to perform. Every new variant adds another flag and another branch.
- **Creation coupled to use.** The function that computes results also decides which concrete objects to create. Adding a new family of objects forces changes in the computation logic.
- **Parallel conditional chains.** Multiple if/elif blocks select related objects together (e.g., picking both an income tax calculator and a capital tax calculator based on the same flag).

```python
# BAD: boolean flags couple creation to use
def compute_tax(
    income: int,
    capital: int,
    apply_floor: bool = True,
) -> int:
    has_capital_tax = True
    use_nl_income_tax = True

    # calculate the tax
    income_tax = (
        calculate_nl_tax(income, apply_floor)
        if use_nl_income_tax
        else calculate_simple_tax(income)
    )
    capital_tax = calculate_capital_tax(capital) if has_capital_tax else 0

    # return the total tax
    return income_tax + capital_tax
```

The compute_tax function is responsible for both selecting which calculators to use and performing the computation. Every new tax system requires modifying this function.

---

## 2. Classic OOP Solution

Build an ABC hierarchy with an abstract factory and concrete factories. This is the Gang of Four version.

### Step 1: Define product ABCs

```python
from abc import ABC, abstractmethod


class IncomeTaxCalculator(ABC):
    @abstractmethod
    def calculate_tax(self, income: int, apply_floor: bool = True) -> int:
        """Calculate income tax."""


class CapitalTaxCalculator(ABC):
    @abstractmethod
    def calculate_tax(self, capital: int) -> int:
        """Calculate capital tax."""
```

### Step 2: Create concrete products

```python
class SimpleIncomeTaxCalculator(IncomeTaxCalculator):
    def calculate_tax(self, income: int, apply_floor: bool = True) -> int:
        return int(income * 0.1)


class NLIncomeTaxCalculator(IncomeTaxCalculator):
    def calculate_tax(self, income: int, apply_floor: bool = True) -> int:
        brackets: list[tuple[int | None, float]] = [
            (69_398_00, 0.37),
            (None, 0.495),
        ]
        taxable_income = income
        if apply_floor:
            taxable_income -= 10_000_00
        total_tax = 0
        for max_income, percentage in brackets:
            bracket_income = min(taxable_income, max_income or taxable_income)
            total_tax += int(bracket_income * percentage)
            taxable_income -= bracket_income
            if taxable_income <= 0:
                break
        return total_tax


class PercentageCapitalTaxCalculator(CapitalTaxCalculator):
    def calculate_tax(self, capital: int) -> int:
        return int(capital * 0.05)


class ZeroCapitalTaxCalculator(CapitalTaxCalculator):
    def calculate_tax(self, capital: int) -> int:
        return 0
```

### Step 3: Define the abstract factory and concrete factories

```python
class TaxFactory(ABC):
    @abstractmethod
    def create_income_tax_calculator(self) -> IncomeTaxCalculator:
        """Creates an income tax calculator."""

    @abstractmethod
    def create_capital_tax_calculator(self) -> CapitalTaxCalculator:
        """Creates a capital tax calculator."""


class SimpleTaxFactory(TaxFactory):
    def create_income_tax_calculator(self) -> IncomeTaxCalculator:
        return SimpleIncomeTaxCalculator()

    def create_capital_tax_calculator(self) -> CapitalTaxCalculator:
        return ZeroCapitalTaxCalculator()


class NLTaxFactory(TaxFactory):
    def create_income_tax_calculator(self) -> IncomeTaxCalculator:
        return NLIncomeTaxCalculator()

    def create_capital_tax_calculator(self) -> CapitalTaxCalculator:
        return PercentageCapitalTaxCalculator()
```

### Step 4: Consumer depends only on the factory abstraction

```python
def compute_tax(
    factory: TaxFactory,
    income: int,
    capital: int,
    apply_floor: bool = True,
) -> int:
    # create the tax calculators
    income_tax_calculator = factory.create_income_tax_calculator()
    capital_tax_calculator = factory.create_capital_tax_calculator()

    # calculate the tax
    income_tax = income_tax_calculator.calculate_tax(income, apply_floor)
    capital_tax = capital_tax_calculator.calculate_tax(capital)

    # return the total tax
    return income_tax + capital_tax


def main():
    factory = NLTaxFactory()
    income = 100_000_00
    capital = 100_000_00
    tax = compute_tax(factory, income, capital)
    print(f"Tax for income ${income/100:.2f} and capital ${capital/100:.2f} is ${tax/100:.2f}")
```

Switching to `SimpleTaxFactory()` changes the entire tax computation system without modifying `compute_tax`.

**Downside:** This introduces many classes. There are two product ABCs, four concrete product classes, one factory ABC, and two concrete factory classes -- eleven classes total for a relatively simple problem.

---

## 3. Pythonic Progression

Start from the classic OOP solution and simplify step by step.

### Step A: Replace ABCs with Protocols

Remove the inheritance relationships. Use structural typing instead of nominal typing.

```python
from typing import Protocol


class IncomeTaxCalculator(Protocol):
    def calculate_tax(self, income: int, apply_floor: bool = True) -> int: ...


class CapitalTaxCalculator(Protocol):
    def calculate_tax(self, capital: int) -> int: ...


class TaxFactory(Protocol):
    def create_income_tax_calculator(self) -> IncomeTaxCalculator: ...
    def create_capital_tax_calculator(self) -> CapitalTaxCalculator: ...
```

The concrete classes remain the same but drop the inheritance. `SimpleIncomeTaxCalculator` no longer inherits from `IncomeTaxCalculator` -- it satisfies the protocol structurally by having a matching `calculate_tax` method. Same for the factory classes: `SimpleTaxFactory` no longer inherits from `TaxFactory`.

**Advantage:** No import dependency between concrete classes and abstract types.

**Same downside:** Still many classes.

### Step B: Replace single-method classes with Callable type aliases

When a product class has only one method, replace it with a function. Define a Callable type alias for the function signature.

```python
from typing import Callable

IncomeTaxCalculator = Callable[[int, bool], int]
CapitalTaxCalculator = Callable[[int], int]
```

Replace the product classes with plain functions:

```python
def calculate_income_tax_simple(
    income: int,
    apply_floor: bool = True,
    tax_rate: float = 0.1,
) -> int:
    return int(income * tax_rate)


def calculate_income_tax_nl(
    income: int,
    apply_floor: bool = True,
) -> int:
    brackets: list[tuple[int | None, float]] = [
        (69_398_00, 0.37),
        (None, 0.495),
    ]
    taxable_income = income
    if apply_floor:
        taxable_income -= 10_000_00
    total_tax = 0
    for max_income, percentage in brackets:
        bracket_income = min(taxable_income, max_income or taxable_income)
        total_tax += int(bracket_income * percentage)
        taxable_income -= bracket_income
        if taxable_income <= 0:
            break
    return total_tax


def calculate_percentage_capital_tax(
    capital: int,
    tax_rate: float = 0.05,
) -> int:
    return int(capital * tax_rate)


def calculate_zero_capital_tax(_: int) -> int:
    return 0
```

**Key insight:** This is only possible because the product classes had a single method. If the products have multiple methods or maintain state, keep using objects.

### Step C: Replace the factory class with a tuple of functions

The factory exists to group related creation functions. A typed tuple does the same thing with no class.

```python
TaxFactory = tuple[IncomeTaxCalculator, CapitalTaxCalculator]

simple_tax_factory: TaxFactory = (
    calculate_income_tax_simple,
    calculate_zero_capital_tax,
)

nl_tax_factory: TaxFactory = (
    calculate_income_tax_nl,
    calculate_percentage_capital_tax,
)
```

The consumer unpacks the tuple:

```python
def compute_tax(
    factory: TaxFactory,
    income: int,
    capital: int,
    apply_floor: bool = True,
) -> int:
    income_tax_calculator, capital_tax_calculator = factory

    income_tax = income_tax_calculator(income, apply_floor)
    capital_tax = capital_tax_calculator(capital)

    return income_tax + capital_tax
```

**Advantage:** Tuples group functions to pass them as a unit, keeping the factory concept without any classes.

### Step D: Use functools.partial to eliminate duplication

Notice that `calculate_income_tax_simple` and `calculate_percentage_capital_tax` both apply a rate to a base amount. Extract a generic function and use `partial` to configure it.

```python
from functools import partial


def calculate_tax_on_rate(
    base: int,
    floor: int = 0,
    tax_rate: float = 0.1,
) -> int:
    taxable_income = max(0, base - floor)
    return int(taxable_income * tax_rate)
```

Now build factories by partially applying the rate:

```python
simple_tax_factory: TaxFactory = (
    calculate_tax_on_rate,
    partial(calculate_tax_on_rate, tax_rate=0),
)

nl_tax_factory: TaxFactory = (
    calculate_income_tax_nl,
    partial(calculate_tax_on_rate, tax_rate=0.05),
)
```

`partial(calculate_tax_on_rate, tax_rate=0)` creates a new callable that behaves like `calculate_zero_capital_tax` but reuses the existing function. The `calculate_zero_capital_tax` function can be deleted entirely.

### Step E: Builder function for full configurability

Wrap the factory tuple creation in a function that accepts configuration parameters. This restores the "factory creates things" feel while staying functional.

```python
IncomeTaxCalculator = Callable[[int], int]
CapitalTaxCalculator = Callable[[int], int]
TaxFactory = tuple[IncomeTaxCalculator, CapitalTaxCalculator]


def create_nl_tax_factory(
    tax_rate: float = 0.05,
    floor: int = 10_000_00,
) -> TaxFactory:
    return (
        partial(calculate_income_tax_nl, floor=floor),
        partial(calculate_tax_on_rate, tax_rate=tax_rate),
    )


def create_simple_tax_factory(
    tax_rate: float = 0.1,
) -> TaxFactory:
    return (
        partial(calculate_tax_on_rate, tax_rate=tax_rate),
        partial(calculate_tax_on_rate, tax_rate=0),
    )
```

The consumer calls the builder at the composition root:

```python
def main():
    income = 100_000_00
    capital = 100_000_00
    tax = compute_tax(create_nl_tax_factory(), income, capital)
    print(f"Tax for income ${income/100:.2f} and capital ${capital/100:.2f} is ${tax/100:.2f}")
```

**Key insight:** The builder function moves configuration-time arguments (rates, floors) out of the Callable type alias. The type aliases become simpler (`Callable[[int], int]`) because the configured parameters are already baked in via `partial`. This also resolves type-checker complaints about default arguments not matching Callable signatures.

### Final form: complete working example

```python
from functools import partial
from typing import Callable

IncomeTaxCalculator = Callable[[int], int]
CapitalTaxCalculator = Callable[[int], int]
TaxFactory = tuple[IncomeTaxCalculator, CapitalTaxCalculator]


def calculate_tax_on_rate(
    base: int,
    floor: int = 0,
    tax_rate: float = 0.1,
) -> int:
    taxable_income = max(0, base - floor)
    return int(taxable_income * tax_rate)


def calculate_income_tax_nl(income: int, floor: int = 0) -> int:
    brackets: list[tuple[int | None, float]] = [
        (69_398_00, 0.37),
        (None, 0.495),
    ]
    taxable_income = max(0, income - floor)
    total_tax = 0
    for max_income, percentage in brackets:
        bracket_income = min(taxable_income, max_income or taxable_income)
        total_tax += int(bracket_income * percentage)
        taxable_income -= bracket_income
        if taxable_income <= 0:
            break
    return total_tax


def create_nl_tax_factory(
    tax_rate: float = 0.05,
    floor: int = 10_000_00,
) -> TaxFactory:
    return (
        partial(calculate_income_tax_nl, floor=floor),
        partial(calculate_tax_on_rate, tax_rate=tax_rate),
    )


def create_simple_tax_factory(tax_rate: float = 0.1) -> TaxFactory:
    return (
        partial(calculate_tax_on_rate, tax_rate=tax_rate),
        partial(calculate_tax_on_rate, tax_rate=0),
    )


def compute_tax(factory: TaxFactory, income: int, capital: int) -> int:
    income_tax_calculator, capital_tax_calculator = factory
    income_tax = income_tax_calculator(income)
    capital_tax = capital_tax_calculator(capital)
    return income_tax + capital_tax


def main():
    income = 100_000_00
    capital = 100_000_00
    tax = compute_tax(create_nl_tax_factory(), income, capital)
    print(
        f"Tax for income ${income / 100:.2f} and capital "
        f"${capital / 100:.2f} is ${tax / 100:.2f}"
    )


if __name__ == "__main__":
    main()
```

---

## 4. When to Use

Apply the Abstract Factory pattern when these signals are present:

- **Multiple boolean flags select related object variants.** A function takes `use_dutch: bool`, `has_capital: bool` to pick among related calculators, formatters, or handlers.
- **Families of objects that vary together.** Switching from "Dutch tax system" to "simple tax system" changes both the income calculator and the capital calculator at the same time.
- **New product families are expected.** The system will grow to support German tax, UK tax, etc. Each new system brings a coordinated set of objects.
- **The consumer does not need to know concrete types.** `compute_tax` should work identically regardless of which tax system is active.
- **Creation logic is scattered across the codebase.** Multiple call sites independently construct the same family of objects.

Do NOT apply when:

- There is only one product (use the Strategy pattern instead).
- Products do not vary as a family (each object is chosen independently).
- The system has exactly two variants and is unlikely to grow (a simple if/else is clearer).

---

## 5. Trade-offs

### Typing system limitations with partial

`functools.partial` does not carry full type information in Python's type system. When a function has default parameters (e.g., `floor: int = 0`) and the Callable type alias does not include that parameter, the type checker may report a mismatch. Specifically:

- A Callable type alias like `Callable[[int], int]` expects exactly one positional int argument.
- A function `def calculate_tax_on_rate(base: int, floor: int = 0, tax_rate: float = 0.1) -> int` has three parameters (two with defaults).
- Assigning this function directly to a variable typed as `Callable[[int], int]` triggers a type error because the signatures do not match exactly.
- `partial(calculate_tax_on_rate, tax_rate=0.05)` returns a `functools.partial[int]` object, which type checkers may not fully resolve against the Callable alias.

**Mitigation strategies:**

1. Move configured parameters into the builder function and use `partial` to bake them in. The Callable alias then only describes the runtime parameters.
2. Use `# type: ignore` sparingly on specific assignments where `partial` creates the mismatch.
3. Accept that the functional approach trades some static type safety for simplicity. If full type safety is critical, keep the Protocol-based approach.

### When builder functions help

Use builder functions when:

- The factory needs configuration parameters (rates, thresholds, connection strings) that should not appear in the Callable type alias.
- Multiple factories share the same structure but differ in configuration.
- The factory creation is complex enough to warrant a named, documented function rather than an inline tuple.

### When the classic approach is still appropriate

Keep the full class-based Abstract Factory when:

- Products have multiple methods, not just one. A `Callable` type alias replaces a single method. An object with `calculate()`, `validate()`, and `summary()` methods cannot be reduced to a single function.
- Products maintain internal state between method calls (e.g., a calculator that accumulates results).
- The codebase requires strict nominal typing and full type-checker coverage without `# type: ignore`.
- The team is more familiar with OOP patterns and readability matters more than conciseness.

### Progression summary

| Approach | Classes | Type safety | Best for |
|---|---|---|---|
| ABC hierarchy | Many (11+) | Full | Multi-method products, shared state |
| Protocol hierarchy | Many (11+) | Full | Same as ABC, but with structural typing |
| Callable type aliases | Zero | Good | Single-method products |
| Tuple of functions | Zero | Good | Grouping related callables |
| partial + tuple | Zero | Partial | Configurable single-method products |
| Builder function + partial | Zero | Partial | Configurable factories at composition root |

---

## 6. Related Patterns

- **Strategy** -- Replaces a single behavioral function. Abstract Factory groups multiple strategies that belong together as a family.
- **Builder** -- Constructs a single complex object step by step. Abstract Factory creates a family of related objects in one shot.
- **Registry** -- Maps string keys to callables for dynamic object creation from configuration data. Use Registry when the factory selection is driven by runtime data (JSON, CLI args).
- **Composition Root** -- The builder function approach naturally fits the composition root, where all concrete wiring happens in one place.
- **functools.partial** -- The core Pythonic tool for the functional factory progression. Bakes in configuration-time arguments to produce callables with simpler runtime signatures.

---

## Quick Decision Guide

```
Do you need to create families of related objects that vary together?
  No  --> Use Strategy pattern for single behavioral swap
  Yes --> Are the products single-method?
            No  --> Use classic ABC/Protocol factory (Section 2, Step A)
            Yes --> Do you need configurable factory parameters?
                      No  --> Use tuple of functions (Section 3, Step C)
                      Yes --> Use builder function + partial (Section 3, Step E)
```
