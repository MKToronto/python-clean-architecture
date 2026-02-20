# Classes and DataClasses Reference

Classes combine data and behavior into a single unit. DataClasses reduce boilerplate for data-oriented classes. Choose the right tool based on whether the class is primarily about behavior or primarily about data.

*Content inspired by Arjan Codes' Software Designer Mindset course.*

---

## 1. Classes vs Data Structures

Built-in data structures (lists, dicts, tuples, sets) focus on a single access pattern: ordered sequences, fast lookup by key, immutable collections. None of them allow attaching custom behavior directly.

A class is a blueprint for objects that bundles data (instance variables) with behavior (methods) that operates on that data. Use a class when:

- The data needs associated operations (reserve a vehicle, process a payment)
- The behavior should live close to the data it modifies (information expert principle)
- The object has identity beyond its data values

Use a plain data structure when:

- The data has no meaningful behavior attached
- A dict, list, tuple, or NamedTuple covers the access pattern
- The structure is temporary or purely for transport

```python
# Plain data structure: no behavior needed
vehicle_data = {
    "brand": "Tesla",
    "model": "Model 3",
    "color": "black",
}

# Class: data + behavior belong together
class Vehicle:
    def __init__(self, brand: str, model: str, color: str):
        self.brand = brand
        self.model = model
        self.color = color

    def reserve(self) -> None:
        print(f"Reserving {self.brand} {self.model}.")

    def generate_license_plate(self) -> None:
        self.license_plate = generate_vehicle_license()
```

---

## 2. Behavior-Focused vs Data-Focused Classes

Every class sits on a spectrum between behavior-focused and data-focused.

**Behavior-focused classes** have few instance variables but many methods. The internal state is an implementation detail. Printing or comparing these objects is rarely useful.

```python
class PaymentProcessor:
    """Behavior-focused: many methods, minimal data."""

    def __init__(self, api_key: str):
        self._api_key = api_key

    def pay_debit(self, order: Order, security_code: str) -> None: ...
    def pay_credit(self, order: Order, security_code: str) -> None: ...
    def refund(self, transaction_id: str) -> None: ...
```

**Data-focused classes** have many instance variables but few methods. Printing, comparing, and inspecting these objects is common and valuable.

```python
class Vehicle:
    """Data-focused: many fields, few methods."""

    def __init__(self, brand: str, model: str, color: str, fuel_type: str):
        self.brand = brand
        self.model = model
        self.color = color
        self.fuel_type = fuel_type

    def reserve(self) -> None:
        print(f"Reserving {self.brand} {self.model}.")
```

Design implications:

| Trait | Behavior-Focused | Data-Focused |
|---|---|---|
| Printing (__repr__) | Rarely needed | Very useful |
| Equality comparison | By identity (default) | By field values |
| Boilerplate __init__ | Minimal | Repetitive |
| DataClass candidate | No | Yes |

Data-focused classes benefit most from the `@dataclass` decorator because it eliminates the repetitive `self.x = x` assignments and provides `__repr__`, `__eq__`, and other dunder methods automatically.

---

## 3. DataClasses

The `@dataclass` decorator from the standard library generates `__init__`, `__repr__`, and `__eq__` methods automatically. Define fields as class-level type annotations instead of writing a manual `__init__`.

```python
from dataclasses import dataclass
from enum import Enum


class FuelType(Enum):
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"


class Accessory(Enum):
    AIRCO = "airco"
    CRUISE_CONTROL = "cruise_control"
    NAVIGATION = "navigation"
    OPEN_ROOF = "open_roof"


@dataclass
class Vehicle:
    brand: str
    model: str
    color: str
    fuel_type: FuelType
    license_plate: str
    accessories: list[Accessory]

    def reserve(self) -> None:
        print(f"Reserving {self.brand} {self.model}.")
```

What `@dataclass` generates:

- `__init__` that accepts all annotated fields as parameters and assigns them to `self`
- `__repr__` that prints all field names and values (e.g., `Vehicle(brand='Tesla', model='Model 3', ...)`)
- `__eq__` that compares two instances by field values

Usage is identical to a regular class:

```python
tesla = Vehicle(
    brand="Tesla",
    model="Model 3",
    color="black",
    fuel_type=FuelType.ELECTRIC,
    license_plate="ABC-123",
    accessories=[Accessory.AIRCO, Accessory.NAVIGATION],
)

print(tesla)
# Vehicle(brand='Tesla', model='Model 3', color='black', fuel_type=<FuelType.ELECTRIC: 'electric'>, ...)

tesla.reserve()
# Reserving Tesla Model 3.
```

Methods work exactly the same as in regular classes. The `@dataclass` decorator only affects initialization and dunder method generation.

---

## 4. Default Values

### Simple defaults

Assign a default value directly in the field annotation. Fields with defaults must come after fields without defaults (same rule as function parameters).

```python
@dataclass
class Vehicle:
    brand: str
    model: str
    color: str
    fuel_type: FuelType = FuelType.ELECTRIC  # simple default
```

### Mutable defaults require field(default_factory=...)

Mutable objects (lists, dicts, sets) cannot be used as direct defaults. This is a safety feature: if a mutable default were shared across instances, modifying it on one instance would affect all others.

```python
from dataclasses import dataclass, field

# WRONG: raises ValueError
@dataclass
class Vehicle:
    accessories: list[Accessory] = []  # not allowed

# CORRECT: use default_factory
@dataclass
class Vehicle:
    brand: str
    model: str
    color: str
    fuel_type: FuelType = FuelType.ELECTRIC
    accessories: list[Accessory] = field(default_factory=list)  # empty list per instance
```

### Custom default factories

The `default_factory` parameter accepts any callable that returns the default value. Define a named function for clarity rather than using a lambda.

```python
# Named function: clear intent, readable
def default_accessories() -> list[Accessory]:
    return [Accessory.AIRCO, Accessory.NAVIGATION]


@dataclass
class Vehicle:
    brand: str
    model: str
    color: str
    fuel_type: FuelType = FuelType.ELECTRIC
    accessories: list[Accessory] = field(default_factory=default_accessories)
```

A lambda works but obscures intent:

```python
# Lambda: works, but harder to read
accessories: list[Accessory] = field(
    default_factory=lambda: [Accessory.AIRCO, Accessory.NAVIGATION]
)
```

Prefer the named function. It documents what the default represents, is easier to test, and reads better in complex class definitions.

### Auto-generated fields via default_factory

Use `default_factory` for any field whose default value requires computation at instance creation time:

```python
import string
import random


def generate_vehicle_license() -> str:
    letters = random.choices(string.ascii_uppercase, k=2)
    digits = random.choices(string.digits, k=3)
    final_letters = random.choices(string.ascii_uppercase, k=2)
    return f"{''.join(letters)}-{''.join(digits)}-{''.join(final_letters)}"


@dataclass
class Vehicle:
    brand: str
    model: str
    color: str
    fuel_type: FuelType = FuelType.ELECTRIC
    license_plate: str = field(default_factory=generate_vehicle_license)
    accessories: list[Accessory] = field(default_factory=list)
```

Each new `Vehicle` instance gets a unique license plate without the caller needing to supply one.

---

## 5. Advanced Initialization

### field(init=False): exclude from __init__

Set `init=False` to prevent a field from appearing in the generated `__init__`. The field still exists on the instance but must be set another way (typically in `__post_init__`).

```python
@dataclass
class Vehicle:
    brand: str
    model: str
    color: str
    fuel_type: FuelType = FuelType.ELECTRIC
    license_plate: str = field(init=False)  # not in __init__
    accessories: list[Accessory] = field(default_factory=list)
```

Attempting to pass `license_plate` to the constructor raises `TypeError: unexpected keyword argument 'license_plate'`. This is useful for fields that should be computed internally, not supplied by the caller.

### __post_init__ for computed fields

The `__post_init__` method runs immediately after the generated `__init__` completes. Use it to compute derived fields, validate inputs, or perform setup that depends on other field values.

```python
@dataclass
class Vehicle:
    brand: str
    model: str
    color: str
    fuel_type: FuelType = FuelType.ELECTRIC
    license_plate: str = field(init=False)
    accessories: list[Accessory] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Compute license plate based on brand
        plate = generate_vehicle_license()
        if self.brand == "Tesla":
            plate += "-T"
        self.license_plate = plate
```

### Validation in __post_init__

Validate field values immediately after construction:

```python
@dataclass
class Vehicle:
    brand: str
    model: str
    color: str
    fuel_type: FuelType = FuelType.ELECTRIC
    license_plate: str = field(default_factory=generate_vehicle_license)
    accessories: list[Accessory] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.brand:
            raise ValueError("Brand cannot be empty.")
        if not self.model:
            raise ValueError("Model cannot be empty.")
```

### Choosing between default_factory and __post_init__

| Scenario | Use |
|---|---|
| Independent default value (empty list, generated ID) | `field(default_factory=...)` |
| Value depends on other fields | `__post_init__` |
| Validation of field values | `__post_init__` |
| Field must not appear in constructor | `field(init=False)` + `__post_init__` |

---

## 6. Frozen DataClasses

Set `frozen=True` to make instances immutable after creation. Any attempt to set an attribute raises `FrozenInstanceError`.

```python
@dataclass(frozen=True)
class Vehicle:
    brand: str
    model: str
    color: str
    fuel_type: FuelType = FuelType.ELECTRIC
    license_plate: str = field(default_factory=generate_vehicle_license)
    accessories: tuple[Accessory, ...] = ()  # use tuple instead of list for true immutability
```

```python
car = Vehicle(brand="BMW", model="5 Series", color="blue")
car.brand = "Tesla"
# FrozenInstanceError: cannot assign to field 'brand'
```

### Use cases for frozen dataclasses

- **Value objects:** Two objects with the same field values are considered equal and interchangeable. Immutability prevents accidental mutation.
- **Dict keys / set members:** Frozen dataclasses are hashable by default (because `__hash__` is generated), making them usable as dict keys or in sets.
- **Thread safety:** Immutable objects are inherently safe to share across threads.

### Limitations

Frozen dataclasses do not allow attribute assignment in `__post_init__`. This means `field(init=False)` combined with assignment in `__post_init__` does not work:

```python
@dataclass(frozen=True)
class Vehicle:
    brand: str
    license_plate: str = field(init=False)

    def __post_init__(self) -> None:
        self.license_plate = generate_vehicle_license()
        # FrozenInstanceError: cannot assign to field 'license_plate'
```

Workaround: use `object.__setattr__` to bypass the frozen guard inside `__post_init__` only, or use `default_factory` instead:

```python
# Option A: default_factory (preferred)
@dataclass(frozen=True)
class Vehicle:
    brand: str
    license_plate: str = field(default_factory=generate_vehicle_license)

# Option B: object.__setattr__ in __post_init__ (when value depends on other fields)
@dataclass(frozen=True)
class Vehicle:
    brand: str
    license_plate: str = field(init=False)

    def __post_init__(self) -> None:
        plate = generate_vehicle_license()
        if self.brand == "Tesla":
            plate += "-T"
        object.__setattr__(self, "license_plate", plate)
```

---

## 7. Encapsulation

DataClasses expose all fields as public attributes by default. This reduces encapsulation because callers can access and modify internal data structures directly.

### The underscore convention

Python has no access modifiers (public/private/protected). Instead, prefix field names with an underscore to signal "internal, do not access directly":

```python
@dataclass
class Vehicle:
    brand: str
    model: str
    color: str
    _fuel_type: FuelType = FuelType.ELECTRIC
    _accessories: list[Accessory] = field(default_factory=list)

    def add_accessory(self, accessory: Accessory) -> None:
        if accessory not in self._accessories:
            self._accessories.append(accessory)

    def has_accessory(self, accessory: Accessory) -> bool:
        return accessory in self._accessories
```

Callers interact through `add_accessory()` and `has_accessory()` rather than touching `_accessories` directly. If the internal storage changes from a list to a set or dict, only the `Vehicle` class needs updating.

### Hiding fields from repr

Use `repr=False` to exclude internal fields from the printed representation:

```python
@dataclass
class Vehicle:
    brand: str
    model: str
    color: str
    _internal_id: str = field(default_factory=generate_vehicle_license, repr=False)
```

```python
print(Vehicle(brand="Tesla", model="Model 3", color="black"))
# Vehicle(brand='Tesla', model='Model 3', color='black')
# _internal_id is hidden from output
```

### Expose behavior, hide data

The core principle: expose what an object can *do* through methods, hide *how* it stores its data behind underscored fields. This allows changing the internal representation without breaking callers.

```python
@dataclass
class VehicleInventory:
    _vehicles: dict[str, Vehicle] = field(default_factory=dict, repr=False)

    def add(self, vehicle: Vehicle) -> None:
        self._vehicles[vehicle.license_plate] = vehicle

    def find_by_plate(self, plate: str) -> Vehicle | None:
        return self._vehicles.get(plate)

    def available_count(self) -> int:
        return len(self._vehicles)
```

Callers never know the internal structure is a dict. Switching to a database-backed store later requires changing only this class.

---

## 8. When to Use What

### Decision guide

**Use a regular class when:**

- The class is primarily about behavior (many methods, few fields)
- Initialization is complex and custom
- The class manages external resources (connections, file handles)
- Printing or comparing instances by field values is not meaningful

**Use @dataclass when:**

- The class is primarily about data (many fields, few methods)
- Automatic `__init__`, `__repr__`, and `__eq__` are useful
- The class represents a value object, DTO, configuration, or data container
- Reducing boilerplate matters

**Use @dataclass(frozen=True) when:**

- The object should be immutable after creation
- The object is a value object (identity determined by field values)
- The object needs to be hashable (dict key, set member)
- Thread safety through immutability is needed

### Quick reference table

| Pattern | Tool | Example |
|---|---|---|
| Service with methods | Regular class | `PaymentProcessor`, `EmailSender` |
| Entity with identity | @dataclass | `Vehicle`, `User`, `Order` |
| Value object (immutable) | @dataclass(frozen=True) | `Money`, `Address`, `Coordinate` |
| Data transfer object | @dataclass | `CreateOrderRequest`, `ApiResponse` |
| Configuration | @dataclass(frozen=True) | `DatabaseConfig`, `AppSettings` |
| Record / row of data | @dataclass | `LogEntry`, `CsvRow` |
| Simple data bag | NamedTuple or dict | Throwaway, no behavior needed |

### Complete example: regular class vs dataclass

```python
from dataclasses import dataclass, field
from enum import Enum


class FuelType(Enum):
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"


class Accessory(Enum):
    AIRCO = "airco"
    CRUISE_CONTROL = "cruise_control"
    NAVIGATION = "navigation"


# Data-focused: use @dataclass
@dataclass
class Vehicle:
    brand: str
    model: str
    color: str
    fuel_type: FuelType = FuelType.ELECTRIC
    license_plate: str = field(default_factory=generate_vehicle_license)
    _accessories: list[Accessory] = field(default_factory=list, repr=False)

    def add_accessory(self, accessory: Accessory) -> None:
        if accessory not in self._accessories:
            self._accessories.append(accessory)

    def list_accessories(self) -> list[Accessory]:
        return list(self._accessories)

    def reserve(self) -> None:
        print(f"Reserving {self.brand} {self.model} [{self.license_plate}].")


# Behavior-focused: use regular class
class RentalService:
    def __init__(self, inventory: list[Vehicle]) -> None:
        self._inventory = inventory
        self._reserved: set[str] = set()

    def reserve(self, license_plate: str) -> None:
        vehicle = self._find(license_plate)
        if vehicle is None:
            raise ValueError(f"Vehicle {license_plate} not found.")
        if license_plate in self._reserved:
            raise ValueError(f"Vehicle {license_plate} already reserved.")
        self._reserved.add(license_plate)
        vehicle.reserve()

    def available_vehicles(self) -> list[Vehicle]:
        return [v for v in self._inventory if v.license_plate not in self._reserved]

    def _find(self, license_plate: str) -> Vehicle | None:
        for vehicle in self._inventory:
            if vehicle.license_plate == license_plate:
                return vehicle
        return None
```

`Vehicle` is data-focused: many fields, printable, comparable by value. `RentalService` is behavior-focused: manages state through methods, has no meaningful `__repr__`, never compared by field values.
