# Layered Architecture Reference

Detailed guide for the three-layer FastAPI architecture: Routers → Operations → Database.

## Architecture Overview

```
┌─────────────────────┐
│   Routers (API)      │  ← Composition root. Injects concrete DB into operations.
│   FastAPI APIRouter   │
└────────┬────────────┘
         │ calls
┌────────▼────────────┐
│   Operations         │  ← Business logic. Accepts DataInterface (Protocol).
│   Pure functions     │     Never imports DB modules directly.
└────────┬────────────┘
         │ calls
┌────────▼────────────┐
│   Database           │  ← Implements DataInterface. Returns DataObject dicts.
│   SQLAlchemy/etc     │     Decoupled from domain via dict[str, Any].
└─────────────────────┘
```

Each layer depends ONLY on the layer directly below. Never skip layers.

---

## Domain Models (Pydantic)

Start by sketching the domain with Pydantic models and dataclasses BEFORE touching frameworks.

### Separate Create vs Read Models

```python
from pydantic import BaseModel

class RoomCreate(BaseModel):
    number: str
    size: int
    price: int

class Room(BaseModel):
    id: str
    number: str
    size: int
    price: int
```

### Separate Update Models (partial updates)

```python
class RoomUpdate(BaseModel):
    number: str | None = None
    size: int | None = None
    price: int | None = None
```

Use `data.model_dump(exclude_none=True)` to get only the fields that were actually provided.

---

## The DataInterface Protocol (Repository Pattern)

The contract between operations and database layers. This is the Repository pattern — an abstraction that separates data access from business logic, allowing operations to work with any data source through a uniform interface:

```python
from typing import Any, Protocol

DataObject = dict[str, Any]

class DataInterface(Protocol):
    def read_by_id(self, id: str) -> DataObject: ...
    def read_all(self) -> list[DataObject]: ...
    def create(self, data: DataObject) -> DataObject: ...
    def update(self, id: str, data: DataObject) -> DataObject: ...
    def delete(self, id: str) -> None: ...
```

### Why dict[str, Any]?

Using plain dicts as the data transfer format decouples operations from ORM models. Operations never see SQLAlchemy objects — they work with plain dicts that can come from any source (SQL, file, API, test stub).

---

## Database Layer

### Generic DBInterface

A single class parameterized by SQLAlchemy model class:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Any

DataObject = dict[str, Any]

class DBInterface:
    def __init__(self, db_session: Session, db_class: type):
        self.db_session = db_session
        self.db_class = db_class

    def read_by_id(self, id: str) -> DataObject:
        obj = self.db_session.get(self.db_class, id)
        if obj is None:
            raise KeyError(f"Not found: {id}")
        return to_dict(obj)

    def read_all(self) -> list[DataObject]:
        objects = self.db_session.scalars(select(self.db_class)).all()
        return [to_dict(obj) for obj in objects]

    def create(self, data: DataObject) -> DataObject:
        obj = self.db_class(**data)
        self.db_session.add(obj)
        self.db_session.commit()
        return to_dict(obj)

    def update(self, id: str, data: DataObject) -> DataObject:
        obj = self.db_session.get(self.db_class, id)
        if obj is None:
            raise KeyError(f"Not found: {id}")
        for key, value in data.items():
            setattr(obj, key, value)
        self.db_session.commit()
        return to_dict(obj)

    def delete(self, id: str) -> None:
        obj = self.db_session.get(self.db_class, id)
        if obj is None:
            raise KeyError(f"Not found: {id}")
        self.db_session.delete(obj)
        self.db_session.commit()
```

### The to_dict Utility

Converts SQLAlchemy model instances to plain dicts:

```python
def to_dict(obj) -> DataObject:
    return {col.name: getattr(obj, col.name) for col in obj.__table__.columns}
```

### SQLAlchemy Models

```python
from sqlalchemy import Column, String, Integer
from db.database import Base

class DBRoom(Base):
    __tablename__ = "rooms"
    id = Column(String, primary_key=True)
    number = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
```

### Database Setup

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
```

---

## Operations Layer

Pure business logic functions. Accept `DataInterface` as a parameter.

```python
from models.room import DataInterface, RoomCreate, Room
from typing import Any
import uuid

DataObject = dict[str, Any]

def read_all_rooms(data_interface: DataInterface) -> list[Room]:
    rooms = data_interface.read_all()
    return [Room(**room) for room in rooms]

def read_room(room_id: str, data_interface: DataInterface) -> Room:
    room = data_interface.read_by_id(room_id)
    return Room(**room)

def create_room(data: RoomCreate, data_interface: DataInterface) -> Room:
    room_data = data.model_dump()
    room_data["id"] = str(uuid.uuid4())
    created = data_interface.create(room_data)
    return Room(**created)

def delete_room(room_id: str, data_interface: DataInterface) -> None:
    data_interface.delete(room_id)
```

### Computed Values in Operations

Operations are where business logic like price computation lives:

```python
def create_booking(data: BookingCreate, data_interface: DataInterface,
                   room_interface: DataInterface) -> Booking:
    room = room_interface.read_by_id(data.room_id)
    nights = (data.to_date - data.from_date).days
    price = nights * room["price"]

    booking_data = data.model_dump()
    booking_data["id"] = str(uuid.uuid4())
    booking_data["price"] = price
    created = data_interface.create(booking_data)
    return Booking(**created)
```

---

## Router Layer (Composition Root)

The router layer is the "single dirty place" — the conceptual composition root where concrete database implementations are chosen and injected into operations.

### Production Approach: FastAPI `Depends()`

Use FastAPI's built-in dependency injection to centralize dependency creation. This avoids repeating `SessionLocal()` and `DBInterface(...)` in every endpoint:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.db_interface import DBInterface
from db.models import DBRoom
from operations import room as room_ops
from models.room import Room, RoomCreate
from typing import Generator

router = APIRouter(prefix="/rooms", tags=["rooms"])


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_room_interface(session: Session = Depends(get_db)) -> DBInterface:
    return DBInterface(session, DBRoom)


@router.get("/", response_model=list[Room])
def read_all_rooms(data_interface: DBInterface = Depends(get_room_interface)):
    return room_ops.read_all_rooms(data_interface)

@router.get("/{room_id}", response_model=Room)
def read_room(room_id: str, data_interface: DBInterface = Depends(get_room_interface)):
    return room_ops.read_room(room_id, data_interface)

@router.post("/", response_model=Room)
def create_room(data: RoomCreate, data_interface: DBInterface = Depends(get_room_interface)):
    return room_ops.create_room(data, data_interface)

@router.delete("/{room_id}")
def delete_room(room_id: str, data_interface: DBInterface = Depends(get_room_interface)):
    return room_ops.delete_room(room_id, data_interface)
```

The dependency provider functions (`get_db`, `get_room_interface`) are the composition root — the single place where concrete wiring decisions are made. In tests, override them via `app.dependency_overrides[get_room_interface] = lambda: mock_interface`.

### Teaching Simplification: Manual Injection

For learning purposes, you may see the simpler pattern of creating dependencies directly in each endpoint:

```python
@router.get("/", response_model=list[Room])
def read_all_rooms():
    session = SessionLocal()
    data_interface = DBInterface(session, DBRoom)
    return room_ops.read_all_rooms(data_interface)
```

This demonstrates the same principle (router as composition root) but repeats the wiring in every endpoint. The `Depends()` approach above is preferred for production code.

### Main App

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from db.database import engine, Base
from routers import rooms, customers, bookings

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(rooms.router)
app.include_router(customers.router)
app.include_router(bookings.router)
```

---

## SQLAlchemy Relationships

When entities reference each other (e.g., a Booking references a Room), use ForeignKey and `relationship()`.

### Defining Relationships

```python
from sqlalchemy import Column, String, Integer, ForeignKey, Date
from sqlalchemy.orm import relationship
from db.database import Base

class DBRoom(Base):
    __tablename__ = "rooms"
    id = Column(String, primary_key=True)
    number = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    bookings = relationship("DBBooking", back_populates="room", cascade="all, delete-orphan")

class DBBooking(Base):
    __tablename__ = "bookings"
    id = Column(String, primary_key=True)
    room_id = Column(String, ForeignKey("rooms.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    price = Column(Integer, nullable=False)
    room = relationship("DBRoom", back_populates="bookings")
```

### Cascade Delete

`cascade="all, delete-orphan"` on the parent side means deleting a Room automatically deletes its Bookings. Use this when child entities have no meaning without the parent.

### Serializing Nested Relationships in `to_dict()`

The basic `to_dict()` only serializes columns. For nested relationships, extend it:

```python
def to_dict(obj, include_relations: list[str] | None = None) -> DataObject:
    result = {col.name: getattr(obj, col.name) for col in obj.__table__.columns}
    if include_relations:
        for rel in include_relations:
            related = getattr(obj, rel, None)
            if isinstance(related, list):
                result[rel] = [to_dict(item) for item in related]
            elif related is not None:
                result[rel] = to_dict(related)
    return result
```

### Eager vs Lazy Loading

By default, SQLAlchemy loads relationships lazily (on first access). This causes N+1 query problems when serializing lists.

```python
from sqlalchemy.orm import joinedload, selectinload

# Eager load in one query (JOIN) — good for single-object fetches
session.execute(select(DBRoom).options(joinedload(DBRoom.bookings)).where(DBRoom.id == room_id)).scalar_one()

# Eager load via separate SELECT — good for list queries (avoids cartesian product)
session.scalars(select(DBRoom).options(selectinload(DBRoom.bookings))).all()
```

**Rule of thumb:** Use `selectinload` for collections (one-to-many), `joinedload` for single objects (many-to-one).

---

## Adding a New Entity Checklist

When adding a new entity (e.g., "bookings") to an existing project:

1. **models/{entity}.py** — Define Pydantic Create, Update, and Read models. Define `DataInterface` Protocol if not using a shared one.
2. **db/models.py** — Add SQLAlchemy model class (e.g., `DBBooking`).
3. **operations/{entity}.py** — Write business logic functions accepting `DataInterface`. Include any computed values.
4. **routers/{entity}.py** — Create `APIRouter`. Wire up endpoints, instantiate `DBInterface`, call operations.
5. **main.py** — `app.include_router(bookings.router)`.
6. **tests/test_{entity}.py** — Create test-specific `DataInterfaceStub` subclass. Test operations without database.
