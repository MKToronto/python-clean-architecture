from sqlalchemy import Column, Date, Integer, String

from db.database import Base


class DBRoom(Base):
    __tablename__ = "rooms"
    id = Column(String, primary_key=True)
    number = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)


class DBCustomer(Base):
    __tablename__ = "customers"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)


class DBBooking(Base):
    __tablename__ = "bookings"
    id = Column(String, primary_key=True)
    room_id = Column(String, nullable=False)
    customer_id = Column(String, nullable=False)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    price = Column(Integer, nullable=False)
