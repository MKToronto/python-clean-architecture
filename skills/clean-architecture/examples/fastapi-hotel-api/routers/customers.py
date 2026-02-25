"""Customer endpoints — composition root for customer operations.

Intentional upgrades from transcript:
  - Same router-level upgrades as rooms.py (see rooms.py docstring)
"""

from fastapi import APIRouter, HTTPException

from db.database import SessionLocal
from db.db_interface import DBInterface
from db.models import DBCustomer
from models.customer import Customer, CustomerCreate
from operations import customer as customer_ops

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_model=list[Customer])
def read_all_customers() -> list[Customer]:
    session = SessionLocal()
    data_interface = DBInterface(session, DBCustomer)
    return customer_ops.read_all_customers(data_interface)


@router.get("/{customer_id}", response_model=Customer)
def read_customer(customer_id: str) -> Customer:
    session = SessionLocal()
    data_interface = DBInterface(session, DBCustomer)
    try:
        return customer_ops.read_customer(customer_id, data_interface)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Customer not found: {customer_id}"
        )


@router.post("/", response_model=Customer, status_code=201)
def create_customer(data: CustomerCreate) -> Customer:
    session = SessionLocal()
    data_interface = DBInterface(session, DBCustomer)
    return customer_ops.create_customer(data, data_interface)


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: str) -> None:
    session = SessionLocal()
    data_interface = DBInterface(session, DBCustomer)
    try:
        customer_ops.delete_customer(customer_id, data_interface)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Customer not found: {customer_id}"
        )
