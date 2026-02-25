from fastapi import APIRouter

from db.database import SessionLocal
from db.db_interface import DBInterface
from db.models import DBCustomer
from models.customer import Customer, CustomerCreate
from operations import customer as customer_ops

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_model=list[Customer])
def read_all_customers():
    session = SessionLocal()
    data_interface = DBInterface(session, DBCustomer)
    return customer_ops.read_all_customers(data_interface)


@router.get("/{customer_id}", response_model=Customer)
def read_customer(customer_id: str):
    session = SessionLocal()
    data_interface = DBInterface(session, DBCustomer)
    return customer_ops.read_customer(customer_id, data_interface)


@router.post("/", response_model=Customer)
def create_customer(data: CustomerCreate):
    session = SessionLocal()
    data_interface = DBInterface(session, DBCustomer)
    return customer_ops.create_customer(data, data_interface)


@router.delete("/{customer_id}")
def delete_customer(customer_id: str):
    session = SessionLocal()
    data_interface = DBInterface(session, DBCustomer)
    customer_ops.delete_customer(customer_id, data_interface)
    return {"detail": "Customer deleted"}
