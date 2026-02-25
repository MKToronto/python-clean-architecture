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
