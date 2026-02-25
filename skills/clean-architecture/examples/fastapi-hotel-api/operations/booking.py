"""Booking business logic — price computation, CRUD orchestration.

Intentional upgrades from transcript:
  - Returns Pydantic Booking models (transcript returned raw DataObject dicts)
  - Uses model_dump() (Pydantic v2) instead of dataclass .dict()
  - "nights" variable name (transcript used "days")
  - data_interface parameter name (transcript used "booking_interface")
  - UUID generation for IDs (transcript relied on DB autoincrement)
  - InvalidDateError validation not included — add if date validation is needed
"""

import uuid

from models.booking import Booking, BookingCreate
from operations.interface import DataInterface


def create_booking(
    data: BookingCreate,
    data_interface: DataInterface,
    room_interface: DataInterface,
) -> Booking:
    room = room_interface.read_by_id(data.room_id)
    nights = (data.to_date - data.from_date).days
    price = nights * room["price"]

    booking_data = data.model_dump()
    booking_data["id"] = str(uuid.uuid4())
    booking_data["price"] = price
    created = data_interface.create(booking_data)
    return Booking(**created)


def read_all_bookings(data_interface: DataInterface) -> list[Booking]:
    bookings = data_interface.read_all()
    return [Booking(**b) for b in bookings]


def read_booking(booking_id: str, data_interface: DataInterface) -> Booking:
    booking = data_interface.read_by_id(booking_id)
    return Booking(**booking)


def delete_booking(booking_id: str, data_interface: DataInterface) -> None:
    data_interface.delete(booking_id)
