# Testable API Reference

How to design FastAPI applications for testability using Protocol-based dependency injection and stub-based testing.

## Core Principle

Operations functions accept a `DataInterface` Protocol parameter. In production, the router passes a real `DBInterface`. In tests, you pass a `DataInterfaceStub`. No database, no mocking library, no test containers needed.

---

## The DataInterfaceStub

A base stub that stores data in a plain dict. Use for all tests.

```python
from typing import Any

DataObject = dict[str, Any]

class DataInterfaceStub:
    def __init__(self):
        self.data: dict[str, DataObject] = {}

    def read_by_id(self, id: str) -> DataObject:
        if id not in self.data:
            raise KeyError(f"Not found: {id}")
        return self.data[id]

    def read_all(self) -> list[DataObject]:
        return list(self.data.values())

    def create(self, data: DataObject) -> DataObject:
        self.data[data["id"]] = data
        return data

    def update(self, id: str, data: DataObject) -> DataObject:
        if id not in self.data:
            raise KeyError(f"Not found: {id}")
        self.data[id].update(data)
        return self.data[id]

    def delete(self, id: str) -> None:
        if id not in self.data:
            raise KeyError(f"Not found: {id}")
        del self.data[id]
```

---

## Writing Tests

### Test Operations Directly

```python
from operations.room import create_room, read_all_rooms, read_room, delete_room
from models.room import RoomCreate

def test_create_room():
    stub = DataInterfaceStub()
    data = RoomCreate(number="101", size=30, price=100)
    room = create_room(data, stub)

    assert room.number == "101"
    assert room.size == 30
    assert room.price == 100
    assert room.id is not None

def test_read_all_rooms_empty():
    stub = DataInterfaceStub()
    rooms = read_all_rooms(stub)
    assert rooms == []

def test_create_and_read_room():
    stub = DataInterfaceStub()
    data = RoomCreate(number="101", size=30, price=100)
    created = create_room(data, stub)
    read = read_room(created.id, stub)
    assert read.number == "101"

def test_delete_room():
    stub = DataInterfaceStub()
    data = RoomCreate(number="101", size=30, price=100)
    created = create_room(data, stub)
    delete_room(created.id, stub)
    rooms = read_all_rooms(stub)
    assert rooms == []
```

### Test Business Logic (Computed Values)

```python
from operations.booking import create_booking
from models.booking import BookingCreate
from datetime import date

def test_booking_price_computed():
    room_stub = DataInterfaceStub()
    room_stub.data["room-1"] = {"id": "room-1", "number": "101", "size": 30, "price": 100}

    booking_stub = DataInterfaceStub()
    data = BookingCreate(
        room_id="room-1",
        customer_id="cust-1",
        from_date=date(2024, 1, 1),
        to_date=date(2024, 1, 4),  # 3 nights
    )
    booking = create_booking(data, booking_stub, room_stub)
    assert booking.price == 300  # 3 nights * 100/night
```

---

## Test-Specific Stub Overrides

For special test scenarios, subclass the base stub:

```python
class FailingCreateStub(DataInterfaceStub):
    def create(self, data: DataObject) -> DataObject:
        raise RuntimeError("Database write failed")

def test_create_room_handles_db_failure():
    stub = FailingCreateStub()
    with pytest.raises(RuntimeError):
        create_room(RoomCreate(number="101", size=30, price=100), stub)
```

```python
class AlwaysEmptyStub(DataInterfaceStub):
    def read_all(self) -> list[DataObject]:
        return []

    def read_by_id(self, id: str) -> DataObject:
        raise KeyError(f"Not found: {id}")
```

---

## Why This Works

1. **No mocking library needed** — The stub is a real class with real behavior. No `unittest.mock`, no `MagicMock`, no fragile mock setup.
2. **Tests are fast** — No database connection, no I/O, pure in-memory dict operations.
3. **Tests are deterministic** — No shared database state between tests. Each test creates its own stub.
4. **Tests verify business logic** — You test what operations *do*, not how they call the database.
5. **Protocol enables this** — Because operations depend on the `DataInterface` Protocol (not a concrete class), any object with the right methods works. The stub satisfies the Protocol structurally.

---

## Error Handling in Tests

### Custom Domain Exceptions

Define domain-specific exception classes:

```python
class NotFoundError(Exception):
    """Raised when a requested entity does not exist."""
    pass

class NotAuthorizedError(Exception):
    """Raised when access to a resource is denied."""
    pass
```

### Operations Raise Domain Exceptions

```python
def read_room(room_id: str, data_interface: DataInterface) -> Room:
    try:
        room = data_interface.read_by_id(room_id)
    except KeyError:
        raise NotFoundError(f"Room not found: {room_id}")
    return Room(**room)
```

### Router Catches and Returns HTTP Status

```python
from fastapi import HTTPException

@router.get("/{room_id}", response_model=Room)
def read_room(room_id: str):
    session = SessionLocal()
    data_interface = DBInterface(session, DBRoom)
    try:
        return room_ops.read_room(room_id, data_interface)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Room not found")
```

### Test Error Cases

```python
def test_read_nonexistent_room():
    stub = DataInterfaceStub()
    with pytest.raises(NotFoundError):
        read_room("nonexistent-id", stub)
```

---

## Unit Testing Practices

Beyond stub-based testing, apply these general practices to write thorough, maintainable tests.

### Test Structure: Arrange-Act-Assert

Every test follows three phases. Keep them visually distinct:

```python
def test_booking_price_for_multiple_nights():
    # Arrange
    stub = DataInterfaceStub()
    stub.data["room-1"] = {"id": "room-1", "price": 150}
    data = BookingCreate(room_id="room-1", from_date=date(2024, 1, 1), to_date=date(2024, 1, 4))

    # Act
    booking = create_booking(data, stub)

    # Assert
    assert booking.price == 450
```

### Test Naming

Name tests to describe the scenario and expected outcome:

```python
# BAD: what does this test?
def test_booking():

# GOOD: scenario and expectation are clear
def test_booking_price_equals_nights_times_room_rate()
def test_create_room_with_duplicate_number_raises_conflict()
def test_delete_nonexistent_room_raises_not_found()
```

### Edge Case Discovery

For any operation, systematically check:

| Category | Examples |
|---|---|
| Empty/zero | Empty list, zero quantity, empty string |
| Boundary | First item, last item, exactly at limit |
| Invalid | Wrong type, missing required field, negative numbers |
| Duplicate | Creating same entity twice, duplicate IDs |
| Not found | Reading/updating/deleting nonexistent entity |
| Overflow | Very large numbers, very long strings |

```python
def test_create_booking_zero_nights():
    stub = DataInterfaceStub()
    stub.data["room-1"] = {"id": "room-1", "price": 100}
    data = BookingCreate(room_id="room-1", from_date=date(2024, 1, 1), to_date=date(2024, 1, 1))
    booking = create_booking(data, stub)
    assert booking.price == 0


def test_read_all_rooms_when_empty():
    stub = DataInterfaceStub()
    rooms = read_all_rooms(stub)
    assert rooms == []
```

### Exception Testing

Use `pytest.raises` to verify that the correct exception is raised with the correct data:

```python
def test_read_nonexistent_room_raises_not_found():
    stub = DataInterfaceStub()
    with pytest.raises(NotFoundError, match="nonexistent-id"):
        read_room("nonexistent-id", stub)


def test_create_booking_invalid_room_raises_not_found():
    stub = DataInterfaceStub()
    data = BookingCreate(room_id="bad-id", from_date=date(2024, 1, 1), to_date=date(2024, 1, 3))
    with pytest.raises(NotFoundError):
        create_booking(data, stub)
```

### Parametrized Tests

When testing the same logic with different inputs, use `pytest.mark.parametrize` instead of duplicating tests:

```python
@pytest.mark.parametrize("nights,expected_price", [
    (1, 100),
    (3, 300),
    (7, 700),
    (0, 0),
])
def test_booking_price_scales_with_nights(nights: int, expected_price: int):
    stub = DataInterfaceStub()
    stub.data["room-1"] = {"id": "room-1", "price": 100}
    start = date(2024, 1, 1)
    end = start + timedelta(days=nights)
    data = BookingCreate(room_id="room-1", from_date=start, to_date=end)
    booking = create_booking(data, stub)
    assert booking.price == expected_price
```

### Test Isolation

Each test must be independent. Never share state between tests:

```python
# BAD: shared stub leaks state between tests
shared_stub = DataInterfaceStub()

def test_create():
    shared_stub.create({"id": "1", "name": "A"})

def test_read_all():
    # fails or passes depending on test execution order
    assert len(shared_stub.read_all()) == 0


# GOOD: each test creates its own stub
def test_create():
    stub = DataInterfaceStub()
    stub.create({"id": "1", "name": "A"})
    assert "1" in stub.data

def test_read_all_empty():
    stub = DataInterfaceStub()
    assert stub.read_all() == []
```

---

## Testing Checklist

When adding tests for a new entity:

1. Create a fresh `DataInterfaceStub()` per test (no shared state)
2. Test CRUD operations: create, read_all, read_by_id, update, delete
3. Test business logic: computed values, validations, edge cases
4. Test error cases: not found, not authorized, invalid data
5. Test boundary cases: empty inputs, zero values, duplicates
6. Test with multiple entities: ensure operations work with populated data
7. Use test-specific stub subclasses for failure scenarios
8. Use `pytest.mark.parametrize` for input/output variations

---

## Refactoring Toward Testability

If you inherit code that is hard to test, follow these four steps to make it testable without rewriting everything:

1. **Identify the dependency** — find the concrete class or global that makes the function hard to test (e.g., a database session created inside the function).
2. **Extract the dependency** — move the creation of that dependency out of the function and accept it as a parameter.
3. **Introduce an abstraction** — define a Protocol for the dependency so the function depends on an interface, not a concrete class.
4. **Inject a stub in tests** — pass a `DataInterfaceStub` (or similar) instead of the real dependency.

```python
# STEP 1: Hard to test — creates its own DB session
def get_room(room_id: str) -> Room:
    session = SessionLocal()
    room = session.get(DBRoom, room_id)
    return Room(**to_dict(room))

# STEP 2: Extract dependency as parameter
def get_room(room_id: str, session: Session) -> Room:
    room = session.get(DBRoom, room_id)
    return Room(**to_dict(room))

# STEP 3: Depend on abstraction (DataInterface Protocol)
def get_room(room_id: str, data_interface: DataInterface) -> Room:
    room = data_interface.read_by_id(room_id)
    return Room(**room)

# STEP 4: Test with stub — no database needed
def test_get_room():
    stub = DataInterfaceStub()
    stub.data["room-1"] = {"id": "room-1", "number": "101", "size": 30, "price": 100}
    room = get_room("room-1", stub)
    assert room.number == "101"
```

---

## Time-Dependent Test Fragility

Tests that depend on the current time are fragile — they may pass at 2pm but fail at midnight. Inject time as a dependency:

```python
# BAD: depends on current time
def is_check_in_today(booking: Booking) -> bool:
    return booking.check_in_date == date.today()

# GOOD: inject "now" as a parameter
def is_check_in_today(booking: Booking, today: date) -> bool:
    return booking.check_in_date == today

# Test with fixed date — always deterministic
def test_check_in_today():
    booking = Booking(check_in_date=date(2024, 6, 15))
    assert is_check_in_today(booking, today=date(2024, 6, 15))
    assert not is_check_in_today(booking, today=date(2024, 6, 16))
```

---

## Skipping and Expected Failures

Use `pytest.mark.skip` and `pytest.mark.xfail` to handle tests that cannot run in all environments:

```python
import pytest

@pytest.mark.skip(reason="Database migration not yet applied")
def test_new_field_exists():
    ...

@pytest.mark.xfail(reason="Known bug in price rounding, fix in next sprint")
def test_price_rounds_correctly():
    ...

@pytest.mark.skipif(sys.platform == "win32", reason="Unix-only feature")
def test_file_permissions():
    ...
```

- **`skip`** — always skips, test is not run
- **`xfail`** — test is expected to fail; if it passes, pytest reports it as `XPASS` (unexpected pass)
- **`skipif`** — conditional skip based on runtime condition

---

## Beyond Unit Tests

For advanced testing techniques beyond the stub-based approach covered here, see **`testing-advanced.md`**:

- **Pytest organization** — `conftest.py` fixtures, CLI options, project structure conventions
- **Property-based testing** with Hypothesis — test properties that hold for any valid input, not just specific examples; catches edge cases humans miss
- **Model-based (stateful) testing** — generate random sequences of operations to find bugs in stateful systems (orders, workflows, state machines)
- **Code coverage philosophy** — why 100% coverage misleads, focus on branch coverage and meaningful assertions over line coverage metrics
