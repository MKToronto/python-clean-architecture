from pydantic import BaseModel


class BookCreate(BaseModel):
    title: str
    author: str
    isbn: str
    price: float


class Book(BaseModel):
    id: int
    title: str
    author: str
    isbn: str
    price: float
