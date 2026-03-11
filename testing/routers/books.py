from fastapi import APIRouter
from services.book_service import create_book, get_all_books, get_book, search_books
from models.book import BookCreate

router = APIRouter()


@router.post("/")
def add_book(data: BookCreate):
    return create_book(data)


@router.get("/")
def list_books():
    return get_all_books()


@router.get("/{book_id}")
def read_book(book_id: int):
    book = get_book(book_id)
    if not book:
        return {"error": "Book not found"}
    return book


@router.get("/search/{query}")
def search(query: str):
    return search_books(query)
