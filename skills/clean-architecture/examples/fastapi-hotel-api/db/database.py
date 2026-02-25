"""Database engine setup and session factory.

Intentional upgrades from transcript:
  - DeclarativeBase class (SQLAlchemy 2.0) replaces legacy declarative_base()
  - Module-level engine replaces init_db(file) function for simplicity
  - SessionLocal naming follows FastAPI convention (transcript used db_session)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./hotel.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass
