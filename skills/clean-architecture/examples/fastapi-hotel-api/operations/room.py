import uuid

from models.room import Room, RoomCreate, RoomUpdate
from operations.interface import DataInterface


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


def update_room(
    room_id: str, data: RoomUpdate, data_interface: DataInterface
) -> Room:
    update_data = data.model_dump(exclude_none=True)
    updated = data_interface.update(room_id, update_data)
    return Room(**updated)


def delete_room(room_id: str, data_interface: DataInterface) -> None:
    data_interface.delete(room_id)
