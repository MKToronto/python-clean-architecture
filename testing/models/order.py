from pydantic import BaseModel


class OrderCreate(BaseModel):
    book_id: int
    quantity: int
    customer_email: str


class Order(BaseModel):
    id: int
    book_id: int
    quantity: int
    customer_email: str
    total: float
    status: str
