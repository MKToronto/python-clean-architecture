from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./bookstore.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class BookModel(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    author = Column(String)
    isbn = Column(String, unique=True)
    price = Column(Float)


class OrderModel(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer)
    quantity = Column(Integer)
    customer_email = Column(String)
    total = Column(Float)
    status = Column(String, default="pending")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
