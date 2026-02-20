import uuid
from typing import Any

from models.room import DataInterface, Room, RoomCreate, RoomUpdate

DataObject = dict[str, Any]


def read_all_rooms(data_interface: DataInterface) -> list[Room]:
    rooms = data_interface.read_all()
    return [Room(**room) for room in rooms]


def read_room(room_id: str, data_interface: DataInterface) -> Room:
    room = data_interface.read_by_id(room_id)
    return Room(**room)


def create_room(data: RoomCreate, data_interface: DataInterface) -> Room:
    room_data = data.dict()
    room_data["id"] = str(uuid.uuid4())
    created = data_interface.create(room_data)
    return Room(**created)


def update_room(
    room_id: str, data: RoomUpdate, data_interface: DataInterface
) -> Room:
    update_data = data.dict(exclude_none=True)
    updated = data_interface.update(room_id, update_data)
    return Room(**updated)


def delete_room(room_id: str, data_interface: DataInterface) -> None:
    data_interface.delete(room_id)
