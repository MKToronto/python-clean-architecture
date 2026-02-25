"""Pydantic request/response models for customers.

Intentional upgrades from transcript:
  - Simplified to name/email (transcript had first_name/last_name/email_address)
  - Pydantic BaseModel (transcript used @dataclass)
"""

from pydantic import BaseModel


class CustomerCreate(BaseModel):
    name: str
    email: str


class Customer(BaseModel):
    id: str
    name: str
    email: str
