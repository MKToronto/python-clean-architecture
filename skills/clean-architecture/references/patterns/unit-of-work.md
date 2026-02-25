# Unit of Work

Group multiple database operations into a single transaction that succeeds or fails atomically. Uses Python's context manager protocol to automatically commit on success and rollback on exception.

---

## The Problem

Multiple related writes must either all succeed or all fail. Without transaction management, a failure midway leaves data in an inconsistent state:

```python
# Dangerous: if add("Banana") fails, "Apple" is already committed
repo.add("Apple", 10)
repo.add("Banana", 20)    # exception here!
repo.add("Cherry", 30)    # never runs
# Database now has Apple but not Banana or Cherry
```

---

## Basic Unit of Work

Track new, modified, and removed objects, then commit them all at once:

```python
from dataclasses import dataclass, field


@dataclass
class User:
    username: str


@dataclass
class UnitOfWork:
    new_users: list[User] = field(default_factory=list)
    dirty_users: list[User] = field(default_factory=list)
    removed_users: list[User] = field(default_factory=list)

    def register_new(self, user: User) -> None:
        self.new_users.append(user)

    def register_dirty(self, user: User) -> None:
        if user not in self.dirty_users:
            self.dirty_users.append(user)

    def register_removed(self, user: User) -> None:
        self.removed_users.append(user)

    def commit(self) -> None:
        for obj in self.new_users:
            print(f"Inserting {obj}")
        for obj in self.dirty_users:
            print(f"Updating {obj}")
        for obj in self.removed_users:
            print(f"Deleting {obj}")
        self.new_users.clear()
        self.dirty_users.clear()
        self.removed_users.clear()
```

This is the conceptual pattern. In practice, the database driver handles tracking.

---

## Context Manager Unit of Work

The Pythonic implementation uses `__enter__`/`__exit__` for automatic transaction lifecycle:

```python
import sqlite3


class Repository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def add(self, name: str, quantity: int) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO items (name, quantity) VALUES (?, ?)", (name, quantity)
        )

    def all(self) -> list[dict]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM items")
        return [dict(row) for row in cursor.fetchall()]


class UnitOfWork:
    def __init__(self, db_name: str = "example.db"):
        self.db_name = db_name
        self.connection: sqlite3.Connection | None = None
        self.repository: Repository | None = None

    def __enter__(self) -> "UnitOfWork":
        self.connection = sqlite3.connect(self.db_name)
        self.connection.execute("BEGIN")
        self.connection.row_factory = sqlite3.Row
        self.repository = Repository(self.connection)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_val:
            self.connection.rollback()   # exception → undo everything
        else:
            self.connection.commit()     # clean exit → save everything
        self.connection.close()
```

Usage — all operations within the `with` block are atomic:

```python
try:
    with UnitOfWork() as uow:
        uow.repository.add("Apple", 10)
        uow.repository.add("Banana", 20)
        # If an exception occurs here, both inserts are rolled back
except Exception as e:
    logging.error(f"Transaction failed: {e}")
```

---

## SQLAlchemy Unit of Work

SQLAlchemy's `Session` already implements Unit of Work internally. Wrap it in a context manager for clean transaction boundaries:

```python
import contextlib
from sqlalchemy.orm import Session, scoped_session, sessionmaker


@contextlib.contextmanager
def unit_of_work():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

```python
with unit_of_work() as session:
    user = User(name="Arjan")
    session.add(user)
    session.flush()  # assigns ID without committing

    user.name = "Arjan Updated"
    # commit happens automatically when with-block exits cleanly
```

---

## Relationship to Our Architecture

In our three-layer architecture, the Unit of Work wraps the database session that `DBInterface` uses:

```
Router (composition root)
  └── creates UnitOfWork context
        └── UnitOfWork provides session to DBInterface
              └── Operations use DBInterface via Protocol
```

The router creates the transaction boundary; operations stay unaware of transaction management.

---

## When to Use

| Use Unit of Work when... | Skip when... |
|---|---|
| Multiple entities must be written atomically | Single-entity CRUD operations |
| Business rule requires all-or-nothing semantics | Database driver handles transactions implicitly |
| You need explicit control over commit/rollback | Simple operations with auto-commit |
| Operations span multiple repositories | One repository per request |

---

## Trade-offs

| Advantage | Cost |
|---|---|
| Atomic transactions — consistent data | Slightly more ceremony than auto-commit |
| Automatic rollback on exceptions | Must ensure all writes go through the UoW |
| Clean boundary between business logic and persistence | Not needed for simple single-write operations |
| Context manager makes the boundary explicit | Connection lifetime tied to `with` block scope |
