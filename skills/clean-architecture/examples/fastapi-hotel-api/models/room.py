from typing import Any, Protocol

from pydantic import BaseModel

DataObject = dict[str, Any]


class DataInterface(Protocol):
    def read_by_id(self, id: str) -> DataObject: ...
    def read_all(self) -> list[DataObject]: ...
    def create(self, data: DataObject) -> DataObject: ...
    def update(self, id: str, data: DataObject) -> DataObject: ...
    def delete(self, id: str) -> None: ...


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
