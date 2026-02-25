"""SQLAlchemy ORM models for the hotel database.

Intentional upgrades from transcript:
  - String UUIDs replace Integer autoincrement IDs (app-generated, portable)
  - Plural table names ("rooms") replace singular ("room") per SQL convention
  - Customer simplified to name/email (transcript had first_name/last_name/email_address)
  - relationship() declarations omitted — not needed when using DataInterface dict pattern
  - Column lengths omitted for SQLite (transcript used String(250))
"""

from sqlalchemy import Column, Date, ForeignKey, Integer, String

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
    room_id = Column(String, ForeignKey("rooms.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    price = Column(Integer, nullable=False)
