from fastapi import FastAPI
from routers.books import router as books_router
from routers.orders import router as orders_router

app = FastAPI(title="Bookstore API")

app.include_router(books_router, prefix="/books", tags=["books"])
app.include_router(orders_router, prefix="/orders", tags=["orders"])
