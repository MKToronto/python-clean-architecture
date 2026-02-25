"""Pydantic request/response models for rooms.

Intentional upgrades from transcript:
  - Entire Pydantic models layer is new — transcript used @dataclass for domain
    models and raw dicts (DataObject) for data transfer
  - RoomUpdate with optional fields enables partial updates via exclude_none=True
  - Separate Create/Update/Read model variants follow FastAPI best practice
"""

from pydantic import BaseModel


class RoomCreate(BaseModel):
    number: str
    size: int
    price: int


class RoomUpdate(BaseModel):
    number: str | None = None
    size: int | None = None
    price: int | None = None


class Room(BaseModel):
    id: str
    number: str
    size: int
    price: int
