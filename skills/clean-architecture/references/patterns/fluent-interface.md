# Fluent Interface Pattern

**Recognize:** Code that builds up a configuration, sequence, or pipeline through multiple calls on the same object. The setup feels clunky, verbose, or error-prone because related properties are set independently.

**Problem:** Sequential operations on an object require separate statements, making the code hard to read and easy to get out of sync (e.g., steps and durations lists that must match length).

> Content inspired by Arjan Codes' video on the Fluent Interface pattern.

---

## Core Idea

A fluent interface is a style where methods return `self` so you can chain them. The goal is readability — the code reads like a sequence of actions, almost like a domain-specific language.

```python
# Without fluent interface
animation = Animation()
animation.add(Rotate(60), duration=1.0)
animation.add(Move(200, 0), duration=1.0)
animation.add(Scale(1.3), duration=0.5)
animation.add(FadeTo(0.0), duration=1.0)

# With fluent interface
animation = (
    Animation()
    .rotate(60)
    .move(200, 0)
    .scale(1.3, duration=0.5)
    .fade_to(0.0)
)
```

---

## Implementation

### Step 1: Return `self` from mutating methods

```python
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Animation:
    steps: list[AnimationStep] = field(default_factory=list)
    durations: list[float] = field(default_factory=list)
    start_time: float = 0.0

    def add(self, step: AnimationStep, duration: float = 1.0) -> Animation:
        self.steps.append(step)
        self.durations.append(duration)
        return self  # enables chaining
```

### Step 2: Add domain-specific verbs

Wrap `add()` with named methods that hide implementation details:

```python
    def rotate(self, degrees: float, duration: float = 1.0) -> Animation:
        return self.add(Rotate(degrees), duration)

    def move(self, dx: float, dy: float, duration: float = 1.0) -> Animation:
        return self.add(Move(dx, dy), duration)

    def scale(self, factor: float, duration: float = 1.0) -> Animation:
        return self.add(Scale(factor), duration)

    def fade_to(self, opacity: float, duration: float = 1.0) -> Animation:
        return self.add(FadeTo(opacity), duration)
```

### Step 3: Use with parenthesized chaining

```python
square_animation = (
    Animation(start_time=0.0)
    .rotate(60)
    .move(200, 0)
    .scale(1.3, duration=0.5)
    .fade_to(0.0)
    .move(-200, 0)
    .fade_to(1.0)
)
```

Reads almost like English: "rotate, then move, then scale, then fade..."

---

## Type Hint for Self-Returning Methods

Use `Self` (Python 3.11+) to support subclassing:

```python
from typing import Self

class Animation:
    def rotate(self, degrees: float, duration: float = 1.0) -> Self:
        self.steps.append(Rotate(degrees))
        self.durations.append(duration)
        return self
```

`Self` ensures subclasses return their own type, not the parent's.

---

## When to Use

**Good fit:**
- Sequential operations where order matters (animations, pipelines, configuration)
- APIs that should read like a story or domain-specific language
- Data pipeline construction (Pandas `.pipe()`, SQLAlchemy query builders)
- Validation chains, configuration flows

**Bad fit:**
- Simple one-off operations — just call a function
- Domains where operations are not naturally sequential
- When you need immutability at each step (fluent interface mutates the object)
- Very long chains that reduce readability
- Out-of-order operations (skip step 2, apply step 5 first)

---

## Fluent Interface vs Builder

These patterns look similar (both use method chaining) but have different intent:

| | Fluent Interface | Builder |
|---|---|---|
| **Intent** | Make API readable as a sequence of actions | Construct a complex object step by step |
| **Result** | The object itself (mutated in place) | A separate product object (via `.build()`) |
| **Mutability** | Mutates the same object | Builder is mutable, product is often immutable |
| **Focus** | Readability and flow | Controlled construction |

The Builder pattern (see `builder.md`) often uses a fluent interface for its API, but the fluent interface pattern is broader — it applies to any API where chaining improves readability.

---

## Real-World Examples in Python

- **Pandas DataFrames:** `df.dropna().groupby("col").mean().reset_index()`
- **SQLAlchemy queries:** `session.query(User).filter(...).order_by(...).limit(10)`
- **httpx/requests:** `client.get(url).raise_for_status().json()`
- **Rich console:** `console.print("[bold red]Error[/]")`

---

## Relationship to Other Patterns

- **Builder** (`builder.md`) — often uses fluent interface; differs in intent (construction vs. readability)
- **Pipeline** (`pipeline.md`) — fluent interfaces naturally express data pipelines
- **Command** (`command.md`) — each chained method could internally create a command object for undo/replay
