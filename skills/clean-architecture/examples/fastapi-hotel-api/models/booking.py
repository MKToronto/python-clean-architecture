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
