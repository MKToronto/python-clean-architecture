"""Customer business logic — CRUD operations.

Intentional upgrades from transcript:
  - Simplified Customer model (name/email) vs transcript (first_name/last_name/email_address)
  - Returns Pydantic Customer models (transcript returned raw DataObject dicts)
  - Customer operations extracted as a standalone module (transcript covered customers
    but did not refactor them into the testable DataInterface pattern)
"""

import uuid

from models.customer import Customer, CustomerCreate
from operations.interface import DataInterface


def read_all_customers(data_interface: DataInterface) -> list[Customer]:
    customers = data_interface.read_all()
    return [Customer(**c) for c in customers]


def read_customer(customer_id: str, data_interface: DataInterface) -> Customer:
    customer = data_interface.read_by_id(customer_id)
    return Customer(**customer)


def create_customer(data: CustomerCreate, data_interface: DataInterface) -> Customer:
    customer_data = data.model_dump()
    customer_data["id"] = str(uuid.uuid4())
    created = data_interface.create(customer_data)
    return Customer(**created)


def delete_customer(customer_id: str, data_interface: DataInterface) -> None:
    data_interface.delete(customer_id)
