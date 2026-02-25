"""Booking endpoints — composition root for booking operations.

Intentional upgrades from transcript:
  - Same router-level upgrades as rooms.py (see rooms.py docstring)
"""

from fastapi import APIRouter, HTTPException

from db.database import SessionLocal
from db.db_interface import DBInterface
from db.models import DBBooking, DBRoom
from models.booking import Booking, BookingCreate
from operations import booking as booking_ops

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/", response_model=list[Booking])
def read_all_bookings() -> list[Booking]:
    session = SessionLocal()
    data_interface = DBInterface(session, DBBooking)
    return booking_ops.read_all_bookings(data_interface)


@router.get("/{booking_id}", response_model=Booking)
def read_booking(booking_id: str) -> Booking:
    session = SessionLocal()
    data_interface = DBInterface(session, DBBooking)
    try:
        return booking_ops.read_booking(booking_id, data_interface)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Booking not found: {booking_id}"
        )


@router.post("/", response_model=Booking, status_code=201)
def create_booking(data: BookingCreate) -> Booking:
    session = SessionLocal()
    data_interface = DBInterface(session, DBBooking)
    room_interface = DBInterface(session, DBRoom)
    try:
        return booking_ops.create_booking(data, data_interface, room_interface)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Room not found: {data.room_id}")


@router.delete("/{booking_id}", status_code=204)
def delete_booking(booking_id: str) -> None:
    session = SessionLocal()
    data_interface = DBInterface(session, DBBooking)
    try:
        booking_ops.delete_booking(booking_id, data_interface)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Booking not found: {booking_id}"
        )
