from fastapi import APIRouter

from db.database import SessionLocal
from db.db_interface import DBInterface
from db.models import DBRoom
from models.room import Room, RoomCreate, RoomUpdate
from operations import room as room_ops

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("/", response_model=list[Room])
def read_all_rooms():
    session = SessionLocal()
    data_interface = DBInterface(session, DBRoom)
    return room_ops.read_all_rooms(data_interface)


@router.get("/{room_id}", response_model=Room)
def read_room(room_id: str):
    session = SessionLocal()
    data_interface = DBInterface(session, DBRoom)
    return room_ops.read_room(room_id, data_interface)


@router.post("/", response_model=Room)
def create_room(data: RoomCreate):
    session = SessionLocal()
    data_interface = DBInterface(session, DBRoom)
    return room_ops.create_room(data, data_interface)


@router.put("/{room_id}", response_model=Room)
def update_room(room_id: str, data: RoomUpdate):
    session = SessionLocal()
    data_interface = DBInterface(session, DBRoom)
    return room_ops.update_room(room_id, data, data_interface)


@router.delete("/{room_id}")
def delete_room(room_id: str):
    session = SessionLocal()
    data_interface = DBInterface(session, DBRoom)
    room_ops.delete_room(room_id, data_interface)
    return {"detail": "Room deleted"}
