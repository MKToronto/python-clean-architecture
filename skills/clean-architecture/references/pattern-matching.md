# Structural Pattern Matching

Python 3.10+ `match`/`case` statements for clean dispatch, destructuring, and type-based branching. Replaces complex if/elif chains when matching against structure, not just values.

> Content inspired by Arjan Codes' structural pattern matching examples.

---

## 1. When to Use

Use `match`/`case` when:
- Branching on the **shape or type** of data (dataclass fields, tuple structure, dict keys)
- Parsing **command strings** with variable arguments
- Handling **multiple message/event types** in a handler
- Replacing **isinstance chains** for type dispatch

Do **not** use when:
- A simple `if/else` or dict lookup suffices (see Strategy pattern → dict lookup)
- You only need equality checks on a single value — a dict is simpler
- You need to support Python < 3.10

---

## 2. Pattern Types

### Literal Patterns

Match exact values:

```python
def handle_command(command: str) -> None:
    match command:
        case "quit":
            print("Quitting.")
        case "reset":
            print("Resetting.")
        case _:
            print(f"Unknown command: {command}")
```

The `_` wildcard matches anything and is the default/fallback case.

### Capture Patterns

Bind matched values to variables:

```python
def handle_command(command: str) -> None:
    match command.split():
        case ["load", filename]:
            print(f"Loading {filename}")
        case ["save", filename]:
            print(f"Saving {filename}")
        case _:
            print(f"Unknown: {command}")
```

`filename` captures whatever string appears in that position.

### OR Patterns

Match any of several alternatives:

```python
match command.split():
    case ["quit" | "exit" | "bye"]:
        print("Goodbye.")
```

### Sequence Patterns with Star

Match variable-length sequences:

```python
match command.split():
    case ["quit" | "exit" | "bye", *rest]:
        # rest captures any trailing arguments
        if "--force" in rest:
            print("Force quitting.")
        else:
            print("Quitting.")
```

### Guard Clauses

Add conditions with `if`:

```python
match command.split():
    case ["quit" | "exit", *rest] if "--force" in rest:
        print("Force quitting.")
    case ["quit" | "exit"]:
        print("Quitting gracefully.")
```

Guards are checked after the pattern matches. If the guard fails, matching continues to the next case.

### Class Patterns

Match against dataclass or class instances by their attributes:

```python
from dataclasses import dataclass

@dataclass
class Command:
    command: str
    arguments: list[str]

def handle(cmd: Command) -> None:
    match cmd:
        case Command(command="load", arguments=[filename]):
            print(f"Loading {filename}")
        case Command(command="save", arguments=[filename]):
            print(f"Saving {filename}")
        case Command(command="quit" | "exit", arguments=["--force" | "-f", *_]):
            print("Force quitting.")
        case Command(command="quit" | "exit"):
            print("Quitting.")
        case _:
            print(f"Unknown: {cmd}")
```

Dataclasses automatically support positional matching via `__match_args__`. For custom classes, define `__match_args__` explicitly:

```python
class Point:
    __match_args__ = ("x", "y")
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

match point:
    case Point(0, 0):
        print("Origin")
    case Point(x, 0):
        print(f"On x-axis at {x}")
    case Point(0, y):
        print(f"On y-axis at {y}")
```

### Numeric Guards

Useful for range-based dispatch:

```python
def classify_amount(amount: float) -> str:
    match amount:
        case x if x < 0:
            return "invalid"
        case 0:
            return "zero"
        case x if x > 10_000:
            return "large"
        case _:
            return "normal"
```

### Mapping Patterns

Match against dict structure:

```python
def handle_event(event: dict) -> None:
    match event:
        case {"type": "click", "x": x, "y": y}:
            print(f"Click at ({x}, {y})")
        case {"type": "keypress", "key": key}:
            print(f"Key pressed: {key}")
        case {"type": "scroll", "direction": "up" | "down" as direction}:
            print(f"Scrolling {direction}")
```

---

## 3. Practical Examples

### API Response Handling

```python
def handle_response(response: dict) -> None:
    match response:
        case {"status": 200, "data": data}:
            process_data(data)
        case {"status": 404}:
            raise NotFoundError()
        case {"status": status} if 400 <= status < 500:
            raise ClientError(status)
        case {"status": status} if status >= 500:
            raise ServerError(status)
```

### Recursive Algorithms

```python
def quick_sort(data: list[int]) -> list[int]:
    match data:
        case []:
            return data
        case [_]:
            return data
        case _:
            pivot = data[-1]
            lower = [x for x in data[:-1] if x <= pivot]
            upper = [x for x in data[:-1] if x > pivot]
            return quick_sort(lower) + [pivot] + quick_sort(upper)
```

### Event Processing

```python
from dataclasses import dataclass

@dataclass
class OrderCreated:
    order_id: str
    customer_id: str

@dataclass
class OrderShipped:
    order_id: str
    tracking_number: str

@dataclass
class OrderCancelled:
    order_id: str
    reason: str

def handle_event(event) -> None:
    match event:
        case OrderCreated(order_id=oid, customer_id=cid):
            send_confirmation(oid, cid)
        case OrderShipped(order_id=oid, tracking_number=tn):
            send_tracking(oid, tn)
        case OrderCancelled(order_id=oid, reason=reason):
            process_refund(oid, reason)
```

---

## 4. Relationship to Other Patterns

### match/case vs Strategy Pattern

- **Strategy** (dict lookup or Callable) — Use when branches represent **swappable algorithms** that should be configurable or extensible.
- **match/case** — Use when branches represent **structural dispatch** where you're matching on shape, type, or nested structure.

```python
# Strategy pattern — different discount algorithms, extensible
discounts: dict[str, DiscountFunction] = {
    "percentage": percentage_discount(0.20),
    "fixed": fixed_discount(10_00),
}
discount = discounts[discount_type]

# match/case — dispatch on event shape, not extensible by config
match event:
    case {"type": "click", "x": x, "y": y}: ...
    case {"type": "keypress", "key": key}: ...
```

### match/case vs if/elif

| Use if/elif when... | Use match/case when... |
|---|---|
| Simple boolean conditions | Matching against structure/shape |
| Comparing against computed values | Destructuring sequences, dicts, or classes |
| Two or three branches | Many branches with complex patterns |
| Need to call functions in conditions | Pattern + guard is enough |

---

## 5. Trade-offs

| Advantage | Limitation |
|---|---|
| Cleaner than isinstance chains | Requires Python 3.10+ |
| Built-in destructuring | Not exhaustive (no compile-time check for missing cases) |
| Readable nested pattern matching | Can be overused for simple equality checks |
| Guards add conditional logic | Performance is comparable to if/elif (not optimized like switch) |

### Exhaustiveness

Python does not enforce exhaustive matching. Always include a `case _` fallback or raise an error:

```python
match status:
    case "active": ...
    case "inactive": ...
    case "pending": ...
    case _:
        raise ValueError(f"Unexpected status: {status}")
```
