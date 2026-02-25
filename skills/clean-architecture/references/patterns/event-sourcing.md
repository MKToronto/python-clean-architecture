# Event Sourcing

Instead of storing current state, store an append-only log of immutable events. Rebuild state by replaying events. Enables audit trails, temporal queries, and derived views (projections) that would be impossible with traditional CRUD.

---

## The Problem

With CRUD, you only have the current state. You can't answer:
- What was the inventory at 3pm yesterday?
- Which items have been added and removed most frequently?
- What sequence of actions led to the current state?

Mutable state overwrites history. Event sourcing preserves it.

---

## Core Components

### Event

An immutable record of something that happened. Generic over the data type:

```python
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class EventType(StrEnum):
    ITEM_ADDED = "item_added"
    ITEM_REMOVED = "item_removed"


@dataclass(frozen=True)
class Event[T = str]:
    type: EventType
    data: T
    timestamp: datetime = datetime.now()
```

**Key properties:**
- `frozen=True` — events are immutable facts; they never change
- Generic `T` — start with `str`, evolve to typed domain objects
- `StrEnum` — prevents typos in event type strings

### Event Store

An append-only log. Events go in; nothing comes out modified:

```python
class EventStore[T]:
    def __init__(self):
        self._events: list[Event[T]] = []

    def append(self, event: Event[T]) -> None:
        self._events.append(event)

    def get_all_events(self) -> list[Event[T]]:
        return list(self._events)
```

---

## Rebuilding State from Events

State is computed by replaying events. Use `Counter` or similar accumulators:

```python
from collections import Counter
from functools import cache


class Inventory:
    def __init__(self, store: EventStore[str]):
        self.store = store

    @cache
    def get_items(self) -> list[tuple[str, int]]:
        counts = Counter[str]()
        for event in self.store.get_all_events():
            if event.type == EventType.ITEM_ADDED:
                counts[event.data] += 1
            elif event.type == EventType.ITEM_REMOVED:
                counts[event.data] -= 1
        return [(item, count) for item, count in counts.items() if count > 0]

    def get_count(self, item: str) -> int:
        return dict(self.get_items()).get(item, 0)

    def _invalidate_cache(self) -> None:
        self.get_items.cache_clear()

    def add_item(self, item: str) -> None:
        self.store.append(Event(EventType.ITEM_ADDED, item))
        self._invalidate_cache()

    def remove_item(self, item: str) -> None:
        if self.get_count(item) <= 0:
            raise ValueError(f"{item} not in inventory")
        self.store.append(Event(EventType.ITEM_REMOVED, item))
        self._invalidate_cache()
```

**Cache pattern:** Use `@cache` on the replay function, invalidate with `cache_clear()` after each write. Reads are fast (cached); writes are still append-only.

---

## Evolving to Typed Events

Start with `Event[str]`, evolve to typed domain objects as the model matures:

```python
@dataclass(frozen=True)
class Item:
    name: str
    rarity: str
    origin: str

# Store now carries rich data
store = EventStore[Item]()
inventory = Inventory(store)

sword = Item(name="sword", rarity="rare", origin="castle")
inventory.add_item(sword)
```

The `EventStore[T]` generic makes this evolution seamless.

---

## Projections

Projections are pure functions that derive specific views from the event stream. They don't modify events — they compute answers:

```python
from collections import Counter, defaultdict


def get_most_collected_items(
    events: list[Event[Item]], top_n: int = 5
) -> list[tuple[str, int]]:
    """Which items were added most often?"""
    counts = Counter[str]()
    for event in events:
        if event.type == EventType.ITEM_ADDED:
            counts[event.data.name] += 1
    return counts.most_common(top_n)


def get_item_origins(events: list[Event[Item]]) -> dict[str, set[str]]:
    """Where did each item come from?"""
    origins: dict[str, set[str]] = defaultdict(set)
    for event in events:
        if event.type == EventType.ITEM_ADDED:
            origins[event.data.name].add(event.data.origin)
    return dict(origins)
```

```python
events = store.get_all_events()
print(get_most_collected_items(events))  # [("sword", 3), ("potion", 2)]
print(get_item_origins(events))          # {"sword": {"castle", "dungeon"}}
```

**Projections are composable:** each is a standalone function over the same event stream. Add new projections without modifying the store or existing code.

---

## When to Use Event Sourcing

| Use event sourcing when... | Use CRUD when... |
|---|---|
| Audit trail is a requirement | Current state is all you need |
| You need temporal queries ("state at time X") | History has no business value |
| Multiple views/projections of same data | One canonical view is sufficient |
| Domain events drive other systems (Pub/Sub) | Simple read/write operations |
| Undo/replay is needed | Operations are straightforward |

---

## Relationship to Other Patterns

- **Pub/Sub** (notification.md) — Events can trigger subscribers. Event sourcing stores the events; Pub/Sub distributes them.
- **CQRS** (cqrs.md) — Natural companion. Write side appends events; read side uses projections.
- **Command** (command.md) — Commands produce events. Commands represent intent; events represent facts.
- **Value Objects** (value-objects.md) — Event data should use value objects for type safety.

---

## Trade-offs

| Advantage | Cost |
|---|---|
| Complete audit trail | More storage (append-only grows) |
| Temporal queries for free | Replay can be slow without snapshots |
| Easy to add new projections | Event schema evolution needs care |
| Natural fit for distributed systems | More complex than CRUD for simple domains |
