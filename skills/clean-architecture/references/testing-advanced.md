# Advanced Testing

Beyond the stub-based unit testing in `testable-api.md`, this file covers pytest organization, property-based testing with Hypothesis, model-based (stateful) testing, and code coverage philosophy.

---

## Pytest Organization

### Project Structure

Mirror the source folder structure in your tests folder:

```
src/
  routers/
    customers.py
  operations/
    customers.py
  db/
    database.py
tests/
  routers/
    test_customers.py
  operations/
    test_customers.py
  db/
    test_database.py
  conftest.py
```

### Naming Conventions

- **Test files:** `test_<module_name>.py` (pytest discovers `test_` prefix by default)
- **Test functions:** `test_<what_it_tests>()` — descriptive names enable keyword filtering
- **One assert per test** — keeps tests focused and failure messages clear

### Useful CLI Options

| Command | Purpose |
|---------|---------|
| `pytest tests/` | Run all tests in folder |
| `pytest tests/test_foo.py::test_bar` | Run a single test |
| `pytest -k "customer and not delete"` | Filter by keyword |
| `pytest -v` | Verbose output with full test names |
| `pytest -s` | Show print/logging output |
| `pytest --durations=10` | Show 10 slowest tests |
| `pytest -x` | Stop on first failure |

### `conftest.py` and Fixtures

Shared test setup goes in `conftest.py`. Pytest auto-discovers it — no imports needed:

```python
# tests/conftest.py
import pytest

@pytest.fixture
def sample_customer() -> dict:
    return {"id": "cust-1", "name": "Jane Doe", "email": "jane@example.com"}

@pytest.fixture
def db_stub() -> DataInterfaceStub:
    return DataInterfaceStub()
```

**Usage in tests:**

```python
def test_get_customer(db_stub, sample_customer):
    db_stub.create(sample_customer)
    result = operations.get_by_id("cust-1", db_stub)
    assert result["name"] == "Jane Doe"
```

### `@pytest.mark.parametrize`

Run the same test with multiple inputs:

```python
@pytest.mark.parametrize("price, quantity, expected", [
    (100, 2, 200),
    (50, 0, 0),
    (0, 5, 0),
    (99, 1, 99),
])
def test_compute_total(price, quantity, expected):
    assert compute_total(price, quantity) == expected
```

Parametrize eliminates copy-paste tests. Use for boundary conditions, equivalence classes, and edge cases.

---

## Property-Based Testing with Hypothesis

Instead of testing specific examples, test **properties** that should hold for any valid input. Hypothesis generates hundreds of random inputs automatically.

### Installation

```bash
pip install hypothesis
```

### Basic Usage

```python
from hypothesis import given, settings, example
from hypothesis.strategies import text, integers

@given(text())
def test_encode_decode_roundtrip(s):
    """Property: decoding an encoded string returns the original."""
    assert decode(encode(s)) == s

@given(integers(min_value=0))
@example(0)  # always test this edge case
@settings(max_examples=200)
def test_price_is_non_negative(price):
    """Property: computed price is never negative."""
    assert compute_discounted_price(price) >= 0
```

### Common Strategies

| Strategy | Generates | Example |
|----------|-----------|---------|
| `text()` | Unicode strings | `"hello"`, `""`, `"\x00"` |
| `integers()` | Arbitrary ints | `0`, `-42`, `2**64` |
| `integers(min_value=1, max_value=100)` | Bounded ints | `1`, `50`, `100` |
| `floats(min_value=0, allow_nan=False)` | Safe floats | `0.0`, `3.14` |
| `sampled_from(["a", "b", "c"])` | Pick from list | `"b"` |
| `lists(integers(), min_size=1)` | Non-empty int lists | `[3, -1, 7]` |

### Custom Composite Strategies

Build complex test data generators:

```python
from hypothesis import composite

@composite
def orders(draw, min_items=1, max_items=5):
    """Generate Order objects with random line items."""
    items = [
        LineItem(
            description=draw(text(min_size=1, max_size=50)),
            price=draw(integers(min_value=1, max_value=10000)),
            quantity=draw(integers(min_value=1, max_value=20)),
        )
        for _ in range(draw(integers(min_value=min_items, max_value=max_items)))
    ]
    return Order(customer="Test", line_items=items)

@given(orders())
def test_order_total_is_sum_of_items(order):
    expected = sum(item.price * item.quantity for item in order.line_items)
    assert order.total == expected
```

### Properties Worth Testing

- **Roundtrip / inverse:** `decode(encode(x)) == x`
- **Invariants:** list length preserved after sort, total equals sum of parts
- **Idempotency:** `f(f(x)) == f(x)` for operations like normalization
- **Commutativity:** `merge(a, b) == merge(b, a)` when order shouldn't matter
- **Bounds:** output is always within expected range

---

## Model-Based (Stateful) Testing

Tests many inputs **with many different action sequences**. Uses a state machine to generate valid sequences of operations and check invariants throughout.

### Testing Pyramid

```
Unit Tests:            one input, one fixed action sequence
Property-Based Tests:  many inputs, one fixed action sequence
Model-Based Tests:     many inputs, many action sequences
```

### Hypothesis Stateful Testing

```python
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, precondition
from hypothesis.strategies import integers, text, sampled_from, data

class OrderStateMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.order = Order(customer="Test")
        self.items: list[LineItem] = []

    @rule(
        description=text(min_size=1),
        price=integers(min_value=1, max_value=10000),
        quantity=integers(min_value=1, max_value=20),
    )
    def create_item(self, description, price, quantity):
        item = LineItem(description, price, quantity)
        self.items.append(item)

    @precondition(lambda self: len(self.items) > 0)
    @rule(data=data())
    def add_item_to_order(self, data):
        item = data.draw(sampled_from(self.items))
        self.order.add_line_item(item)

    @precondition(lambda self: len(self.order.line_items) > 0)
    @rule(data=data())
    def remove_item_from_order(self, data):
        item = data.draw(sampled_from(self.order.line_items))
        self.order.remove_line_item(item)

    @invariant()
    def total_is_correct(self):
        expected = sum(i.price * i.quantity for i in self.order.line_items)
        assert self.order.total == expected

    @precondition(lambda self: len(self.order.line_items) == 0)
    @invariant()
    def empty_order_has_zero_total(self):
        assert self.order.total == 0

# Pytest discovery
TestOrder = OrderStateMachine.TestCase
```

### Key Components

| Component | Purpose |
|-----------|---------|
| `RuleBasedStateMachine` | Base class — Hypothesis generates sequences of `@rule` calls |
| `@rule` | An action Hypothesis can apply (with generated arguments) |
| `@invariant` | Checked after every rule — must always hold |
| `@precondition` | Rule only applies when condition is true |
| `data()` strategy | Allows drawing from dynamic state (e.g., `sampled_from(self.items)`) |

**Why it's powerful:** Hypothesis found bugs where the same item added twice to an order caused incorrect totals — a sequence humans rarely think to test.

---

## Code Coverage Philosophy

### What Coverage Measures

Coverage tracks which lines of code were **executed** during tests — not whether they were **correctly validated**.

```bash
pip install pytest-cov
pytest --cov=src --cov-report=html tests/
```

### Why 100% Coverage Misleads

A function can have 100% line coverage and still contain critical bugs:

```python
def compute_tax(price: int, exemption: int, rate: float) -> float:
    return (price - exemption) * rate  # 100% covered!
    # BUG: returns negative tax when exemption > price
    # FIX: return max(0, (price - exemption) * rate)
```

Tests that execute this line achieve coverage — but only a test with `exemption > price` catches the bug.

### What to Focus On

1. **Branch coverage** over line coverage — test both sides of every `if/else`
2. **Edge cases and boundaries** — zero, negative, empty, maximum values
3. **Error paths** — test that exceptions are raised for invalid input
4. **Meaningful assertions** — `assert result == expected`, not just `assert result`

### Practical Guidelines

- **Aim for 80-90% meaningful coverage**, not 100% meaningless coverage
- Use coverage reports to **find untested code paths**, not as a quality metric
- **Unit tests must be deterministic** — never use `random.randint()` or `random.choice()` as test input; use fixed values so failures reproduce identically in CI
- **Property-based tests (Hypothesis) are a controlled exception** — Hypothesis uses seeds, shrinking, and a failure database to ensure reproducibility despite generating varied inputs. This is fundamentally different from naive randomness.
- Combine coverage with property-based testing to catch bugs that example-based tests miss

---

## Relationship to Other Testing Approaches

- **`testable-api.md`** covers stub-based unit testing with `DataInterfaceStub` — the foundation for testing operations without a database
- **Property-based testing** complements stubs: use stubs for isolation, Hypothesis for input variety
- **Model-based testing** is most valuable for stateful systems (orders, workflows, state machines from `patterns/state.md`)
