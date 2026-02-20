from pydantic import BaseModel


class CustomerCreate(BaseModel):
    name: str
    email: str


class Customer(BaseModel):
    id: str
    name: str
    email: str
