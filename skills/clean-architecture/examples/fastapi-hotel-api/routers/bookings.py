from fastapi import APIRouter

from db.database import SessionLocal
from db.db_interface import DBInterface
from db.models import DBBooking, DBRoom
from models.booking import Booking, BookingCreate
from operations import booking as booking_ops

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/", response_model=list[Booking])
def read_all_bookings():
    session = SessionLocal()
    data_interface = DBInterface(session, DBBooking)
    return booking_ops.read_all_bookings(data_interface)


@router.get("/{booking_id}", response_model=Booking)
def read_booking(booking_id: str):
    session = SessionLocal()
    data_interface = DBInterface(session, DBBooking)
    return booking_ops.read_booking(booking_id, data_interface)


@router.post("/", response_model=Booking)
def create_booking(data: BookingCreate):
    session = SessionLocal()
    data_interface = DBInterface(session, DBBooking)
    room_interface = DBInterface(session, DBRoom)
    return booking_ops.create_booking(data, data_interface, room_interface)


@router.delete("/{booking_id}")
def delete_booking(booking_id: str):
    session = SessionLocal()
    data_interface = DBInterface(session, DBBooking)
    booking_ops.delete_booking(booking_id, data_interface)
    return {"detail": "Booking deleted"}
