"""Room endpoints — composition root for room operations.

Intentional upgrades from transcript:
  - APIRouter(prefix=, tags=) for OpenAPI grouping (transcript used bare APIRouter)
  - HTTPException 404 error handling (transcript had none)
  - Explicit status_code (201, 204) on create/delete routes
  - response_model declarations for automatic serialization
  - Function names without api_ prefix (transcript used api_read_all_rooms etc.)
  - Session created per-request and injected (transcript used global db_session)
"""

from fastapi import APIRouter, HTTPException

from db.database import SessionLocal
from db.db_interface import DBInterface
from db.models import DBRoom
from models.room import Room, RoomCreate, RoomUpdate
from operations import room as room_ops

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("/", response_model=list[Room])
def read_all_rooms() -> list[Room]:
    session = SessionLocal()
    data_interface = DBInterface(session, DBRoom)
    return room_ops.read_all_rooms(data_interface)


@router.get("/{room_id}", response_model=Room)
def read_room(room_id: str) -> Room:
    session = SessionLocal()
    data_interface = DBInterface(session, DBRoom)
    try:
        return room_ops.read_room(room_id, data_interface)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Room not found: {room_id}")


@router.post("/", response_model=Room, status_code=201)
def create_room(data: RoomCreate) -> Room:
    session = SessionLocal()
    data_interface = DBInterface(session, DBRoom)
    return room_ops.create_room(data, data_interface)


@router.put("/{room_id}", response_model=Room)
def update_room(room_id: str, data: RoomUpdate) -> Room:
    session = SessionLocal()
    data_interface = DBInterface(session, DBRoom)
    try:
        return room_ops.update_room(room_id, data, data_interface)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Room not found: {room_id}")


@router.delete("/{room_id}", status_code=204)
def delete_room(room_id: str) -> None:
    session = SessionLocal()
    data_interface = DBInterface(session, DBRoom)
    try:
        room_ops.delete_room(room_id, data_interface)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Room not found: {room_id}")
