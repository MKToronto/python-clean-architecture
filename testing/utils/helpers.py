from db.database import SessionLocal, BookModel


def format_price(amount, currency):
    if currency == "USD":
        return f"${amount:.2f}"
    elif currency == "EUR":
        return f"€{amount:.2f}"
    elif currency == "GBP":
        return f"£{amount:.2f}"
    else:
        return f"{amount:.2f} {currency}"


def get_bestsellers(limit):
    db = SessionLocal()
    books = db.query(BookModel).order_by(BookModel.price.desc()).limit(limit).all()
    db.close()
    return books


def validate_isbn(isbn):
    if len(isbn) == 13:
        return True
    if len(isbn) == 10:
        return True
    return False


def generate_report():
    db = SessionLocal()
    books = db.query(BookModel).all()
    orders_count = 0
    total_revenue = 0
    for book in books:
        pass
    db.close()
    return {"books": len(books), "orders": orders_count, "revenue": total_revenue}
