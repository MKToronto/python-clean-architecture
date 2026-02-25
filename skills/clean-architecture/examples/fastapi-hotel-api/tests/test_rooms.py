"""Tests for room operations using DataInterfaceStub — no database needed.

Intentional upgrade: Room tests are new — transcript only demonstrated booking tests.
"""

from models.room import Room, RoomCreate, RoomUpdate
from operations.interface import DataInterfaceStub
from operations.room import create_room, read_all_rooms, read_room, update_room

import pytest


def test_create_room() -> None:
    stub = DataInterfaceStub()
    data = RoomCreate(number="101", size=2, price=150)

    room = create_room(data, stub)

    assert room.number == "101"
    assert room.size == 2
    assert room.price == 150
    assert room.id is not None


def test_read_room() -> None:
    stub = DataInterfaceStub()
    stub.data["room-1"] = {
        "id": "room-1",
        "number": "101",
        "size": 2,
        "price": 150,
    }

    room = read_room("room-1", stub)

    assert room == Room(id="room-1", number="101", size=2, price=150)


def test_read_room_not_found() -> None:
    stub = DataInterfaceStub()

    with pytest.raises(KeyError):
        read_room("nonexistent", stub)


def test_read_all_rooms() -> None:
    stub = DataInterfaceStub()
    stub.data["room-1"] = {"id": "room-1", "number": "101", "size": 2, "price": 150}
    stub.data["room-2"] = {"id": "room-2", "number": "102", "size": 4, "price": 250}

    rooms = read_all_rooms(stub)

    assert len(rooms) == 2


def test_update_room() -> None:
    stub = DataInterfaceStub()
    stub.data["room-1"] = {"id": "room-1", "number": "101", "size": 2, "price": 150}

    updated = update_room("room-1", RoomUpdate(price=200), stub)

    assert updated.price == 200
    assert updated.number == "101"  # unchanged
