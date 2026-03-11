from db.database import SessionLocal, BookModel
from models.book import BookCreate, Book


def create_book(data: BookCreate) -> Book:
    db = SessionLocal()
    book = BookModel(**data.dict())
    db.add(book)
    db.commit()
    db.refresh(book)
    db.close()
    return Book(id=book.id, title=book.title, author=book.author, isbn=book.isbn, price=book.price)


def get_all_books():
    db = SessionLocal()
    books = db.query(BookModel).all()
    db.close()
    result = []
    for b in books:
        result.append({"id": b.id, "title": b.title, "author": b.author, "isbn": b.isbn, "price": b.price})
    return result


def get_book(book_id):
    db = SessionLocal()
    book = db.query(BookModel).filter(BookModel.id == book_id).first()
    db.close()
    if book:
        return {"id": book.id, "title": book.title, "author": book.author, "isbn": book.isbn, "price": book.price}
    return None


def search_books(query):
    db = SessionLocal()
    books = db.query(BookModel).filter(BookModel.title.contains(query)).all()
    db.close()
    return [{"id": b.id, "title": b.title, "author": b.author} for b in books]
