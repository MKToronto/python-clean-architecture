# Pipeline Pattern

> Content inspired by Arjan Codes' Pythonic Patterns course.

## Problem

Sequential transformations on data or sequential handling of events require a structured way to compose and order operations. Naive nesting of function calls becomes unreadable, and adding, removing, or reordering steps requires editing deeply nested code.

```python
def add_three(x: float) -> float:
    return x + 3

def multiply_by_two(x: float) -> float:
    return x * 2

def main() -> None:
    # Nesting reads inside-out and does not scale
    result = multiply_by_two(multiply_by_two(add_three(add_three(15))))
    print(result)  # 72
```

Adding more steps means wrapping more parentheses. The order of operations reads right-to-left. There is no data structure to inspect, reorder, or dynamically modify the sequence.

---

## Chain of Responsibility -- Handler Class with Propagation Control

The closest GoF pattern to a pipeline is Chain of Responsibility. Each handler holds a reference to the next handler. A request propagates through the chain, and each handler decides whether to process it and whether to forward it.

### Implementation

```python
from __future__ import annotations
from abc import ABC, abstractmethod


class Handler(ABC):
    def __init__(self) -> None:
        self.next: Handler | None = None

    def set_next(self, handler: Handler) -> None:
        self.next = handler

    @abstractmethod
    def on_click(self) -> bool:
        """Handle the click. Return True to propagate, False to stop."""
        ...

    def handle_click_event(self) -> None:
        """Process this handler, then propagate if on_click returns True."""
        if self.on_click() and self.next:
            self.next.handle_click_event()


class Button(Handler):
    def __init__(self, name: str = "button", disabled: bool = False) -> None:
        super().__init__()
        self.name = name
        self.disabled = disabled

    def on_click(self) -> bool:
        if self.disabled:
            return True  # Cannot handle, propagate to next
        print(f"Button {self.name} was clicked")
        return False  # Handled, stop propagation


class Panel(Handler):
    def __init__(self, name: str = "panel") -> None:
        super().__init__()
        self.name = name

    def on_click(self) -> bool:
        # Panel does not handle clicks, always propagate
        return True


class Window(Handler):
    def __init__(self, name: str = "window") -> None:
        super().__init__()
        self.name = name

    def on_click(self) -> bool:
        print(f"Window {self.name} handled the click")
        return False  # Final handler, stop propagation
```

### Usage

```python
def main() -> None:
    button = Button(disabled=False)
    panel = Panel()
    window = Window()

    # Build the chain: button -> panel -> window
    button.set_next(panel)
    panel.set_next(window)

    # Click propagates through the chain
    button.handle_click_event()
    # Output: "Button button was clicked"

    # With button disabled, click reaches the window
    button.disabled = True
    button.handle_click_event()
    # Output: "Window window handled the click"
```

Key mechanics:
- `on_click()` returns a boolean: `True` means propagate to the next handler, `False` means stop.
- `handle_click_event()` is the non-abstract method that orchestrates: call `on_click()`, then conditionally forward.
- The chain is a linked list built via `set_next()`.
- Use an ABC here (not a Protocol) because the base class stores state (`self.next`) and provides the shared `handle_click_event()` method.

---

## Pythonic Pipeline -- Function Composition with functools.reduce

Replace the handler class hierarchy with plain functions and compose them into a pipeline using `functools.reduce`.

### Core Compose Function

```python
from functools import reduce, partial
from typing import Callable

# Type alias: any function that takes a float and returns a float
ComposableFunction = Callable[[float], float]


def compose(*functions: ComposableFunction) -> ComposableFunction:
    """Compose functions left-to-right into a single pipeline function."""
    return reduce(
        lambda f, g: lambda x: g(f(x)),
        functions,
    )
```

How `reduce` builds the composition:
1. Start with the first two functions `f` and `g`.
2. Produce a new function `lambda x: g(f(x))` that applies `f` first, then `g`.
3. Pair that result with the next function in the sequence and repeat.
4. The final result is a single function that applies all steps left-to-right.

### Usage

```python
def add_three(x: float) -> float:
    return x + 3


def multiply_by_two(x: float) -> float:
    return x * 2


def add_n(x: float, n: float) -> float:
    return x + n


def main() -> None:
    # Compose a pipeline of operations
    my_pipeline = compose(add_three, add_three, multiply_by_two, multiply_by_two)
    result = my_pipeline(15)
    print(result)  # 72

    # Use partial to supply extra arguments
    pipeline_with_partial = compose(
        partial(add_n, n=100),
        multiply_by_two,
        add_three,
    )
    result = pipeline_with_partial(15)
    print(result)  # (15 + 100) * 2 + 3 = 233
```

Advantages over nested calls:
- Operations read left-to-right in declaration order.
- The pipeline is a data structure (a sequence of functions) that can be built dynamically.
- `functools.partial` fills in configuration arguments so each step matches the `ComposableFunction` signature.
- Adding, removing, or reordering steps means changing the argument list to `compose()`.

---

## Pandas Integration -- the .pipe() Method

Pandas DataFrames have a built-in `.pipe()` method that combines function composition with partial application. Each step receives a DataFrame, performs a transformation, and returns a DataFrame.

```python
import pandas as pd


def mean_age_by_group(df: pd.DataFrame, column: str) -> pd.DataFrame:
    return df.groupby(column).mean(numeric_only=True)


def uppercase_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [col.upper() for col in df.columns]
    return df


def main() -> None:
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie", "Diana"],
            "group": ["A", "B", "A", "B"],
            "age": [30, 25, 35, 28],
        }
    )

    result = (
        df
        .pipe(mean_age_by_group, column="group")
        .pipe(uppercase_column_names)
    )
    print(result)
```

`.pipe(func, *args, **kwargs)` calls `func(df, *args, **kwargs)` and returns the result. This is equivalent to composing functions with partial application but uses method chaining syntax familiar to pandas users.

---

## When to Use Existing Libraries vs Custom Pipelines

For simple sequential transformations (data cleaning, image processing steps), the `compose()` helper or `.pipe()` chaining is sufficient.

For complex pipeline requirements, use an existing framework instead of building your own:
- **Luigi** -- pipeline framework for batch processing with dependency resolution.
- **Apache Airflow** -- DAG-based workflow orchestration with scheduling, monitoring, and distributed execution.

Complex features that justify a framework:
- Circuit breakers to halt on errors.
- Async operations with API calls.
- Parallel or DAG-based execution (not just linear).
- Scheduling and retry logic.
- Multi-server or GPU/CPU resource allocation.
- Batching and buffering.

If your UI framework already provides event propagation, use its built-in mechanism rather than implementing Chain of Responsibility from scratch.

---

## When to Use / Trade-offs

**Use Chain of Responsibility when:**
- Handlers need individual state (e.g., a UI component's disabled flag).
- Propagation control matters -- each handler decides whether to forward the event.
- The framework or domain naturally models a linked chain (UI hierarchies, middleware stacks).

**Use function composition when:**
- Each step is a pure transformation: input goes in, output comes out.
- Steps are stateless or their state is captured via `partial` / closures.
- You want to dynamically build, reorder, or inspect the pipeline at runtime.

**Trade-offs:**
- Chain of Responsibility uses an ABC with stored state. It is heavier but gives each handler autonomy over propagation.
- Function composition is lightweight but assumes uniform function signatures. Use a type alias (`ComposableFunction`) to enforce this.
- `functools.reduce` can be hard to read for developers unfamiliar with functional programming. The `compose()` helper encapsulates this complexity so callers never see `reduce` directly.
- Pandas `.pipe()` is idiomatic for DataFrame workflows but is not a general-purpose pipeline mechanism.
- For anything beyond simple linear steps, reach for a dedicated library rather than growing a custom pipeline.
