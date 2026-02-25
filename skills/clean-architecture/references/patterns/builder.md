# Builder Pattern

Separate the construction of a complex object from its representation. A mutable builder accumulates configuration via a fluent API, then produces an immutable final product via `.build()`.

---

## The Problem

Complex objects with many optional parts lead to constructors with too many parameters, or require multiple steps that must happen in a specific order:

```python
# Hard to read, easy to get wrong
page = HTMLPage(
    title="My Page",
    metadata={"author": "Arjan", "description": "Demo"},
    body_elements=[
        "<h1>Hello</h1>",
        "<p>Some text</p>",
        "<button onclick=\"location.href='#'\">Click</button>",
    ],
)
```

---

## Fluent Builder

Each method returns `Self` for chaining. The builder is mutable; the product is immutable:

```python
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class HTMLPage:
    """Immutable final product."""
    title: str
    metadata: dict[str, str]
    body_elements: list[str]

    def render(self) -> str:
        body = "\n".join(self.body_elements)
        meta = "\n".join(
            f'<meta name="{k}" content="{v}">' for k, v in self.metadata.items()
        )
        return f"<html><head><title>{self.title}</title>{meta}</head><body>{body}</body></html>"


class HTMLBuilder:
    """Mutable builder with fluent API."""

    def __init__(self) -> None:
        self._title: str = "Untitled"
        self._body: list[str] = []
        self._metadata: dict[str, str] = {}

    def set_title(self, title: str) -> Self:
        self._title = title
        return self

    def add_header(self, text: str, level: int = 1) -> Self:
        self._body.append(f"<h{level}>{text}</h{level}>")
        return self

    def add_paragraph(self, text: str) -> Self:
        self._body.append(f"<p>{text}</p>")
        return self

    def add_button(self, label: str, onclick: str = "#") -> Self:
        self._body.append(
            f"<button onclick=\"location.href='{onclick}'\">{label}</button>"
        )
        return self

    def add_metadata(self, name: str, content: str) -> Self:
        self._metadata[name] = content
        return self

    def build(self) -> HTMLPage:
        return HTMLPage(self._title, self._metadata, self._body)
```

Usage reads as a declarative specification:

```python
page = (
    HTMLBuilder()
    .set_title("Builder Pattern Demo")
    .add_header("Hello from Python!", level=1)
    .add_paragraph("This page was generated using the Builder Pattern.")
    .add_button("Visit Site", onclick="https://example.com")
    .build()
)
```

---

## Key Mechanics

### `Self` Return Type

Each builder method returns `Self` (from `typing`), enabling method chaining. This is the standard Python type for fluent APIs since Python 3.11.

### Mutable Builder → Immutable Product

The builder accumulates state in mutable private attributes. `.build()` freezes the result into a `frozen=True` dataclass. After building, the product cannot be modified.

### Defaults

The builder can provide sensible defaults (e.g., `title = "Untitled"`). The caller only specifies what they care about.

---

## Real-World Builders in Python

The builder pattern appears in many Python libraries:

```python
# pandas styled DataFrame
styled = (
    df.style
    .set_caption("Styled DataFrame")
    .highlight_max(axis=0)
    .format("{:.2f}")
    .background_gradient(cmap="viridis")
)

# matplotlib figure
fig, ax = plt.subplots()
ax.bar(fruits, counts, label=labels, color=colors)
ax.set_ylabel("supply")
ax.set_title("Fruit supply")
ax.legend(title="Color")
```

---

## When to Use the Builder

| Use builder when... | Use `@dataclass` with defaults when... |
|---|---|
| Many optional parts that vary independently | All fields are known at construction time |
| Construction order matters | No ordering constraints |
| Product should be immutable after construction | Mutability is fine |
| Fluent API improves readability | Simple keyword args are clear enough |
| Different representations from same construction process | One representation is sufficient |

**Pythonic note:** In Python, keyword arguments and dataclasses with default values handle most construction scenarios. The builder pattern adds value when construction involves sequential steps, computed intermediate values, or when the fluent API significantly improves readability.

---

## Builder vs Fluent Interface

The builder pattern and fluent interfaces both use method chaining, but they are not the same thing:

- **Builder** — separates construction from representation. A mutable builder accumulates state, then `.build()` produces an immutable product. The builder and product are different objects.
- **Fluent Interface** — any API that returns `self` from methods to enable chaining. The chained object may or may not produce a separate product.

```python
# Builder: separate builder → product
page = HTMLBuilder().set_title("Demo").add_paragraph("Hello").build()  # returns HTMLPage

# Fluent Interface (NOT a builder): modifies the same object
query = Query().select("name").where("age > 18").order_by("name")  # returns Query
```

Many Python libraries (pandas, matplotlib, SQLAlchemy query API) use fluent interfaces without being builders. The distinction matters because a builder enforces a construction/usage phase boundary that a plain fluent interface does not.

---

## Design Notes

- **Rule of thumb:** Consider a builder when objects have 5+ optional configuration attributes, or when construction involves sequential steps with computed intermediate values.
- **Forgetting `.build()`:** A common mistake is using the builder object as if it were the product. The builder is mutable and may not have the same interface. Make the product class clearly different (e.g., `frozen=True` dataclass) so the type checker catches this.
- **Validation in `.build()`:** The builder can validate that required parts were set before constructing the product. Raise `ValueError` with a clear message if a required part is missing.

```python
def build(self) -> HTMLPage:
    if not self._body:
        raise ValueError("Cannot build an empty page — add at least one element")
    return HTMLPage(self._title, self._metadata, list(self._body))
```

---

## Trade-offs

| Advantage | Cost |
|---|---|
| Readable, declarative construction | Extra class (builder + product) |
| Immutable final product | Builder is a mutable intermediate |
| Flexible — callers configure only what they need | Overkill for simple objects |
| Enforces valid construction (build validates) | Slightly more code than a constructor |
