"""Tests for booking operations using DataInterfaceStub — no database needed.

Follows the pattern from Arjan Codes' Designing a Testable API course:
create stub implementations, then test pure business logic directly.

Intentional upgrades from transcript:
  - pytest (transcript used unittest with class-based TestCase)
  - Generic DataInterfaceStub used directly (transcript created custom subclasses
    like RoomInterface(DataInterfaceStub) and BookingInterface(DataInterfaceStub))
  - Asserts on Pydantic model attributes (transcript asserted on dict keys)
  - Tests KeyError for room-not-found (transcript tested InvalidDateError instead)
  - Room tests in separate test_rooms.py (transcript only showed booking tests)
"""

from datetime import date

from models.booking import Booking, BookingCreate
from operations.booking import create_booking
from operations.interface import DataInterfaceStub

import pytest


def make_room_stub(price: int = 150) -> DataInterfaceStub:
    """Create a room stub with a single room at the given price."""
    stub = DataInterfaceStub()
    stub.data["room-1"] = {
        "id": "room-1",
        "number": "101",
        "size": 2,
        "price": price,
    }
    return stub


def test_price_one_night() -> None:
    booking_stub = DataInterfaceStub()
    room_stub = make_room_stub(price=150)

    data = BookingCreate(
        room_id="room-1",
        customer_id="cust-1",
        from_date=date(2024, 12, 24),
        to_date=date(2024, 12, 25),
    )

    booking = create_booking(data, booking_stub, room_stub)

    assert booking.price == 150  # 1 night × $150


def test_price_multiple_nights() -> None:
    booking_stub = DataInterfaceStub()
    room_stub = make_room_stub(price=100)

    data = BookingCreate(
        room_id="room-1",
        customer_id="cust-1",
        from_date=date(2024, 12, 20),
        to_date=date(2024, 12, 25),
    )

    booking = create_booking(data, booking_stub, room_stub)

    assert booking.price == 500  # 5 nights × $100


def test_booking_stored_in_stub() -> None:
    booking_stub = DataInterfaceStub()
    room_stub = make_room_stub(price=150)

    data = BookingCreate(
        room_id="room-1",
        customer_id="cust-1",
        from_date=date(2024, 12, 24),
        to_date=date(2024, 12, 25),
    )

    booking = create_booking(data, booking_stub, room_stub)

    # Verify the booking was persisted via the stub
    assert booking.id in booking_stub.data


def test_room_not_found() -> None:
    booking_stub = DataInterfaceStub()
    room_stub = DataInterfaceStub()  # empty — no rooms

    data = BookingCreate(
        room_id="nonexistent",
        customer_id="cust-1",
        from_date=date(2024, 12, 24),
        to_date=date(2024, 12, 25),
    )

    with pytest.raises(KeyError):
        create_booking(data, booking_stub, room_stub)
