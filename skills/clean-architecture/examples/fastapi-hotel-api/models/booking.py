"""Pydantic request/response models for bookings.

Intentional upgrades from transcript:
  - Pydantic BaseModel replaces @dataclass BookingCreateData
  - Class name BookingCreate (transcript used BookingCreateData)
  - String IDs (transcript used int)
  - Defined in separate models/ directory (transcript defined in operations file)
"""

from datetime import date

from pydantic import BaseModel


class BookingCreate(BaseModel):
    room_id: str
    customer_id: str
    from_date: date
    to_date: date


class Booking(BaseModel):
    id: str
    room_id: str
    customer_id: str
    from_date: date
    to_date: date
    price: int
