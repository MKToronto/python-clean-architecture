# Data Structures Reference

Choosing the right data structure is a design decision, not an afterthought. Each data structure has trade-offs in performance, memory, and expressiveness that directly shape your software architecture.

> Content inspired by Arjan Codes' Software Designer Mindset course.

---

## 1. Core Principle

Do not reach for a list or dictionary at random. Ask these questions first:

1. **What operations do I perform most?** Search, iteration, insertion, grouping?
2. **What is the semantic meaning?** Ordered sequence, key-value mapping, unique collection, fixed set of options?
3. **What are the performance constraints?** O(1) lookup required? Memory-constrained? Real-time?
4. **What is clearest to read?** The data structure should communicate intent to other developers.

A wrong choice cascades. Pick a list where you need frequent search, and you pay O(n) on every lookup. Pick a dictionary where you need ordered iteration, and you carry unnecessary memory overhead. The data structure is the foundation -- get it right early.

---

## 2. Lists

Ordered, mutable sequences of items. The workhorse collection in Python.

### Characteristics

- Indexed access and slicing (`my_list[1:3]`)
- Variable length -- grows and shrinks automatically
- Can hold any type of object
- O(n) search -- must scan linearly to find an element
- Higher overhead than raw arrays due to dynamic resizing

### When to Use

- Ordered collections where sequence matters (line items in an order, commands to execute in sequence)
- Iterating over every element in the collection
- Small to medium collections where search performance is not critical

### When NOT to Use

- Frequent search by value -- use a dictionary instead
- Large numerical datasets -- use NumPy arrays (fixed size, contiguous memory, much faster)
- Need unique elements only -- use a set instead

### Code Examples

```python
# Create and slice a list
items = [10, 20, 30, 40, 50]
first_two = items[:2]     # [10, 20]
from_third = items[2:]    # [30, 40, 50]

# Copy a list (shallow copy via slice)
items_copy = items[:]
items_copy[0] = -100
print(items)       # [10, 20, 30, 40, 50] -- original unchanged
print(items_copy)  # [-100, 20, 30, 40, 50]

# Negative indexing
last = items[-1]   # 50
```

### Performance Note

Python lists are not arrays. They maintain metadata (length, capacity) and store references to objects scattered in memory. For large numerical workloads, use NumPy:

```python
import numpy as np

# NumPy array: contiguous memory, typed, fast vectorized operations
prices = np.array([19.99, 29.99, 9.99, 49.99])
discounted = prices * 0.9  # vectorized -- no Python loop needed
```

---

## 3. Dictionaries

Hash-based key-value mappings with O(1) lookup. The go-to structure when you need fast search.

### Characteristics

- Implemented as hash tables -- keys are hashed to memory locations
- O(1) constant-time lookup regardless of size
- Higher memory overhead than lists (must store keys and hash metadata)
- Keys must be hashable (strings, integers, tuples -- not lists or dicts)

### When to Use

- Frequent lookup by key (registries, caches, configuration)
- Collections searchable by name or ID (game objects, HTML elements by ID, presets by name)
- Replacing if/elif chains with dictionary mappings

### When NOT to Use

- Primarily iterating over every element with no search -- use a list (less overhead)
- Large collections where memory matters -- dictionaries carry extra cost per entry
- Ordered sequences where position is the primary access pattern

### Code Examples

```python
# Dictionary for fast lookup
vehicle_data: dict[str, int] = {
    "compact": 30_00,
    "sedan": 50_00,
    "suv": 75_00,
}

price = vehicle_data["sedan"]  # O(1) lookup -- instant regardless of dict size

# Registry pattern with dictionary
from typing import Callable

handlers: dict[str, Callable[[], None]] = {
    "start": handle_start,
    "stop": handle_stop,
    "restart": handle_restart,
}

def dispatch(command: str) -> None:
    handler = handlers[command]  # O(1) -- no if/elif chain
    handler()
```

### Comparison: List Search vs Dictionary Lookup

```python
# List: O(n) -- scans every element
users_list = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
user = next(u for u in users_list if u["id"] == 2)  # linear scan

# Dictionary: O(1) -- direct hash lookup
users_dict = {1: "Alice", 2: "Bob"}
user = users_dict[2]  # constant time
```

---

## 4. Tuples

Immutable, heterogeneous groupings. Use them to return or pass a small bundle of related values.

### Characteristics

- Immutable -- cannot change values after creation
- Typically hold values of different types (unlike lists which are usually homogeneous)
- Faster access than object instance variables
- Hashable (can be used as dictionary keys, unlike lists)

### When to Use

- Returning multiple values from a function (2-3 related values)
- Grouping heterogeneous values that belong together temporarily
- Dictionary keys when you need a composite key

### When NOT to Use

- More than 2-3 values -- use a dataclass or named tuple instead (positional access becomes confusing)
- Ordered homogeneous collections -- use a list
- When the caller needs to understand what each position means without reading the function signature

### Code Examples

```python
from enum import Enum

class Month(Enum):
    JAN = 1
    FEB = 2
    # ... etc
    JUN = 6

def get_birthday() -> tuple[Month, int]:
    """Return birth month and year."""
    return Month.JUN, 1977

# Unpack directly -- clear and readable
month, year = get_birthday()
print(f"Born: {month.name} {year}")
```

### When to Upgrade to a Class

```python
# BAD: tuple with too many fields -- what does position 3 mean?
employee = ("Alice", 47, "Engineering", 95_000, True)

# GOOD: dataclass with named fields
from dataclasses import dataclass

@dataclass
class Employee:
    name: str
    id: int
    department: str
    salary: int
    is_active: bool

employee = Employee(name="Alice", id=47, department="Engineering", salary=95_000, is_active=True)
```

---

## 5. Sets

Unordered collections of unique elements with fast membership testing.

### Characteristics

- No duplicate elements -- adding a duplicate is silently ignored
- O(1) membership testing (`x in my_set`)
- Unordered -- no indexing or slicing
- Support set operations: union, intersection, difference

### When to Use

- Deduplication of elements
- Fast membership testing ("is this user ID in the active set?")
- Mathematical set operations (finding common elements between collections)

### Frozen Sets

Use `frozenset` when you need an immutable set -- required for using sets as dictionary keys or elements of other sets.

### Code Examples

```python
# Deduplicate a list
raw_tags = ["python", "api", "python", "rest", "api"]
unique_tags = set(raw_tags)  # {"python", "api", "rest"}

# Fast membership testing
active_user_ids: set[int] = {101, 202, 303, 404}

def is_active(user_id: int) -> bool:
    return user_id in active_user_ids  # O(1)

# Set operations
backend_skills = {"python", "sql", "docker"}
frontend_skills = {"javascript", "css", "docker"}

shared = backend_skills & frontend_skills      # {"docker"}
all_skills = backend_skills | frontend_skills   # union of both
only_backend = backend_skills - frontend_skills # {"python", "sql"}

# Frozen set as dictionary key
permissions: dict[frozenset[str], str] = {
    frozenset({"read", "write"}): "editor",
    frozenset({"read"}): "viewer",
}
```

---

## 6. Enums

Replace string constants with strong typing. Never use plain strings for enumerated values.

### The Problem with Strings

Strings offer no compile-time safety. A typo, a capitalization error, or an accidental translation silently produces wrong behavior:

```python
# BAD: string-based -- no type safety
def is_birthday_month(month: str) -> bool:
    return month == "June"

is_birthday_month("june")    # False -- capitalization mismatch
is_birthday_month("Juni")    # False -- wrong language, no error raised
is_birthday_month("Juen")    # False -- typo, no error raised
```

### The Enum Solution

Define a finite set of valid options as an Enum. The type checker catches invalid values before runtime:

```python
from enum import Enum, auto

class Month(Enum):
    JAN = auto()
    FEB = auto()
    MAR = auto()
    APR = auto()
    MAY = auto()
    JUN = auto()
    JUL = auto()
    AUG = auto()
    SEP = auto()
    OCT = auto()
    NOV = auto()
    DEC = auto()

def is_birthday_month(month: Month) -> bool:
    return month == Month.JUN

# Type checker catches this immediately:
is_birthday_month(Month.JUN)      # True -- correct
is_birthday_month(Month.JUEN)     # ERROR: Month has no member "JUEN"
is_birthday_month("June")         # ERROR: expected Month, got str
```

### When to Use

- Stages in a pipeline (training, validation, testing)
- Status codes (pending, active, completed, cancelled)
- Configuration options with a fixed set of choices
- Any place you would otherwise use string constants for a limited set of values

### Practical Patterns

```python
from enum import Enum

class ExperimentStage(Enum):
    TRAINING = "training"
    VALIDATION = "validation"
    TESTING = "testing"

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"

# Use in type hints -- the function signature communicates valid inputs
def run_experiment(stage: ExperimentStage) -> None:
    match stage:
        case ExperimentStage.TRAINING:
            train_model()
        case ExperimentStage.VALIDATION:
            validate_model()
        case ExperimentStage.TESTING:
            test_model()
```

---

## 7. Strings

Immutable text sequences. Behave like lists but cannot be modified in place.

### Characteristics

- Immutable -- cannot assign to an index (`my_str[0] = "X"` raises `TypeError`)
- Support slicing and indexing like lists
- No distinction between a character and a string -- a character is a string of length 1
- Single quotes and double quotes are interchangeable
- Triple quotes for multi-line strings

### When to Use

- Representing text data
- Keys in dictionaries
- Display and formatting

### Do NOT Use For

- Representing a finite set of options -- use an Enum instead
- Structured data with multiple fields -- use a dataclass

### Code Examples

```python
text = "Hello, World!"

# Indexing and slicing -- same as lists
print(text[0])      # "H"
print(text[-1])     # "!"
print(text[7:12])   # "World"

# Membership testing
print("World" in text)  # True

# Immutability -- the variable can be reassigned, but the string value cannot be mutated
text = "Different string"  # fine -- reassigns the variable
# text[0] = "d"           # TypeError: 'str' does not support item assignment
```

### F-Strings (Formatted String Literals)

Use f-strings for all string formatting. They are clearer than `%` formatting or `.format()`:

```python
name = "Alice"
amount_cents = 30_000

# f-string -- clean and readable
greeting = f"Hello, {name}!"
price = f"Total: ${amount_cents / 100:.2f}"

print(greeting)  # "Hello, Alice!"
print(price)     # "Total: $300.00"

# Avoid old-style formatting
# BAD: "Hello, %s" % name
# BAD: "Hello, {}".format(name)
# GOOD: f"Hello, {name}"
```

---

## 8. Numeric Types

Integers and floats have fundamentally different trade-offs. Choose based on precision and performance needs.

### Integers

- **Variable-length** in Python -- no fixed maximum value (limited only by available memory)
- **Exact precision** -- no rounding errors
- **Slower for very large values** -- more bytes needed, more computation time
- **Cannot represent fractions** directly

### Floats

- **Fixed 64-bit** representation (1 sign bit, 11 exponent bits, 52 significand bits)
- **Fast computation** -- hardware-optimized floating-point operations
- **Less precise** -- multiplication and division can lose precision in significant digits
- **Can represent fractions** (approximately)

### When to Use Each

| Use Integers When | Use Floats When |
|---|---|
| Financial systems (store cents, not dollars) | Real-time physics simulations |
| Counting discrete items | Scientific computation where speed matters |
| Exact arithmetic required | Approximate values are acceptable |
| IDs, indices, quantities | Measurements, coordinates, percentages |

### Code Examples

```python
# Financial system -- use integers for precision
price_cents = 1999        # $19.99 stored as cents
tax_cents = 160           # $1.60
total_cents = price_cents + tax_cents  # 2159 -- exact
print(f"Total: ${total_cents / 100:.2f}")  # "$21.59"

# BAD: float arithmetic loses precision
price = 19.99
tax = 1.60
total = price + tax  # 21.590000000000003 -- floating-point error

# Real-time system -- use floats for speed
position_x = 145.732
velocity = 3.5
dt = 0.016  # 16ms frame time
position_x += velocity * dt  # fast, approximate -- good enough for rendering
```

---

## 9. Decision Framework

Use this table as a quick reference when choosing a data structure:

| Dominant Need | Best Structure | Why |
|---|---|---|
| Ordered iteration over items | `list` | Maintains insertion order, indexed access |
| Fast search by key | `dict` | O(1) hash-based lookup |
| Return 2-3 related values | `tuple` | Lightweight, immutable grouping |
| Unique elements / membership test | `set` | O(1) membership, automatic deduplication |
| Fixed set of valid options | `Enum` | Type safety, catches errors at check time |
| Large numerical arrays | `numpy.ndarray` | Contiguous memory, vectorized operations |
| Text data | `str` | Immutable, rich slicing and formatting |
| Exact arithmetic | `int` | Variable precision, no rounding |
| Fast approximate arithmetic | `float` | Hardware-optimized 64-bit operations |

### Decision Flow

1. **Is it a fixed set of options?** Use `Enum`. Do not use strings.
2. **Do you need fast lookup by key?** Use `dict`.
3. **Do you need unique elements?** Use `set`.
4. **Is order important?** Use `list`.
5. **Are you grouping 2-3 heterogeneous values?** Use `tuple`. If more, use a `dataclass`.
6. **Is it a large numerical dataset?** Use `numpy.ndarray`.
7. **Need exact money/counting?** Use `int`. Need fast approximation? Use `float`.

### The Upgrade Path

Data structures evolve as requirements grow:

```
tuple (2-3 fields)  -->  @dataclass (named fields)  -->  class (with behavior)
list (small)        -->  dict (need search)          -->  database (need persistence)
str constants       -->  Enum (need type safety)
list of numbers     -->  numpy.ndarray (need performance)
```

Always start with the simplest structure that meets current needs. Upgrade when the trade-offs demand it.
