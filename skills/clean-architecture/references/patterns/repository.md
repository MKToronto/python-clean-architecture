# Repository Pattern

**Recognize:** Data access logic (SQL queries, file I/O, API calls) is mixed into domain classes or scattered across the codebase. Changing the storage backend requires modifying business logic.

**Problem:** Tight coupling between data representation and data storage makes code hard to test, hard to extend, and impossible to swap storage backends without rewriting operations.

> Content inspired by Arjan Codes' deep dive into the Repository pattern.

---

## Core Idea

The Repository pattern separates **how you store data** from **how you access data**. A repository provides a collection-like interface (get, add, update, delete) that hides the storage mechanism behind it.

```
Operations (business logic)
    │
    ▼
Repository Interface (Protocol)    ← abstract contract
    │
    ├── SQLRepository              ← SQL implementation
    ├── FileRepository             ← file-based implementation
    └── InMemoryRepository         ← test stub
```

---

## Before: Coupled Data + Storage

```python
@dataclass
class Post:
    id: str
    title: str
    content: str

    @classmethod
    def get_by_id(cls, post_id: str, db_path: str) -> "Post":
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        row = cursor.fetchone()
        conn.close()
        return Post(id=row[0], title=row[1], content=row[2])

    @classmethod
    def add(cls, post: "Post", db_path: str) -> None:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO posts VALUES (?, ?, ?)",
                       (post.id, post.title, post.content))
        conn.commit()
        conn.close()
```

Problems:
- `Post` knows about SQLite, connection strings, SQL syntax
- Can't test without a real database
- Switching to NoSQL or file storage means rewriting `Post`
- Every entity class duplicates the same SQL boilerplate

---

## After: Repository Pattern

### 1. Pure domain model

```python
@dataclass
class Post:
    id: str
    title: str
    content: str
```

No storage details. Just data.

### 2. Repository interface

```python
from typing import Protocol

class PostRepository(Protocol):
    def get(self, post_id: str) -> Post: ...
    def get_all(self) -> list[Post]: ...
    def add(self, post: Post) -> None: ...
    def update(self, post: Post) -> None: ...
    def delete(self, post_id: str) -> None: ...
```

### 3. Concrete implementation

```python
import sqlite3

class SQLitePostRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_table()

    def _create_table(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS posts (id TEXT PRIMARY KEY, title TEXT, content TEXT)"
            )

    def get(self, post_id: str) -> Post:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if row is None:
            raise KeyError(f"Post not found: {post_id}")
        return Post(id=row[0], title=row[1], content=row[2])

    def get_all(self) -> list[Post]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM posts").fetchall()
        return [Post(id=r[0], title=r[1], content=r[2]) for r in rows]

    def add(self, post: Post) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO posts VALUES (?, ?, ?)",
                         (post.id, post.title, post.content))

    def update(self, post: Post) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE posts SET title = ?, content = ? WHERE id = ?",
                         (post.title, post.content, post.id))

    def delete(self, post_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
```

---

## Testing with a Mock Repository

```python
class InMemoryPostRepository:
    def __init__(self) -> None:
        self.posts: dict[str, Post] = {}

    def get(self, post_id: str) -> Post:
        if post_id not in self.posts:
            raise KeyError(f"Post not found: {post_id}")
        return self.posts[post_id]

    def get_all(self) -> list[Post]:
        return list(self.posts.values())

    def add(self, post: Post) -> None:
        self.posts[post.id] = post

    def update(self, post: Post) -> None:
        if post.id not in self.posts:
            raise KeyError(f"Post not found: {post.id}")
        self.posts[post.id] = post

    def delete(self, post_id: str) -> None:
        if post_id not in self.posts:
            raise KeyError(f"Post not found: {post_id}")
        del self.posts[post_id]
```

Pass `InMemoryPostRepository` to operations in tests — no database needed. This is exactly the same pattern as `DataInterfaceStub` in the three-layer architecture.

---

## Relationship to DataInterface

The plugin's `DataInterface` Protocol + `DBInterface` implementation **is** the Repository pattern:

| Repository Pattern | Three-Layer Architecture |
|---|---|
| Repository (Protocol) | `DataInterface` |
| Concrete Repository | `DBInterface` |
| Mock Repository | `DataInterfaceStub` |
| Domain Model | Pydantic models |

The `DataInterface` is a generic repository — it works with `DataObject = dict[str, Any]` rather than typed domain objects. This trades type safety for flexibility (one `DBInterface` class serves all entities).

---

## Generic Repository (Python 3.12+)

For a typed repository that works with any model:

```python
class Repository[T](Protocol):
    def get(self, id: str) -> T: ...
    def get_all(self) -> list[T]: ...
    def add(self, item: T) -> None: ...
    def update(self, item: T) -> None: ...
    def delete(self, id: str) -> None: ...
```

---

## When to Use

- **Use it** when you need to swap storage backends, test without a database, or decouple business logic from persistence
- **Skip it** when an ORM like SQLAlchemy already provides the abstraction you need and you won't switch backends
- **Be aware** that a repository limits you to the methods you define — complex queries may need a query builder or raw SQL alongside the repository

## Relationship to Other Patterns

- **Unit of Work** (`unit-of-work.md`) — wraps multiple repository operations in a transaction
- **Adapter** (`adapter.md`) — a repository implementation is effectively an adapter between your domain and the storage system
- **DataInterface** (`references/layered-architecture.md`) — the three-layer architecture's version of the Repository pattern
