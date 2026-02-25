# Pydantic Validation

How to validate, transform, and constrain data using Pydantic v2 validators, field constraints, and model configuration. Covers field validators, model validators, serializers, and integration with FastAPI.

> **Python 3.11+** required for `Self` type hint used in model validators. For 3.10, use `from __future__ import annotations` or `from typing_extensions import Self`.

> Content inspired by Arjan Codes' Pydantic examples.

---

## 1. Field Constraints

The simplest validation — use `Field()` parameters to constrain values without writing any validator code.

### Numeric Constraints

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str
    price: int = Field(gt=0)                    # greater than 0
    tax_percent: float = Field(ge=0, le=1)       # 0.0 to 1.0
    quantity: int = Field(ge=0, default=0)        # non-negative, defaults to 0
```

| Parameter | Meaning |
|---|---|
| `gt` | Greater than |
| `ge` | Greater than or equal |
| `lt` | Less than |
| `le` | Less than or equal |
| `multiple_of` | Must be a multiple of this value |

### String Constraints

```python
class User(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    code: str = Field(pattern=r"^[A-Z]{3}-\d{4}$")  # regex pattern
```

### Collection Constraints

```python
from pydantic import Field
from uuid import UUID

class Team(BaseModel):
    members: list[UUID] = Field(default_factory=list, max_length=500)
    tags: set[str] = Field(default_factory=set, min_length=1)
```

### Field Metadata

```python
class User(BaseModel):
    name: str = Field(
        description="Full name of the user",
        examples=["Alice Smith"],
    )
    email: EmailStr = Field(
        description="Email address",
        examples=["user@example.com"],
        frozen=True,  # immutable after creation
    )
    id: UUID4 = Field(default_factory=uuid4, kw_only=True)
```

---

## 2. Field Validators

Use `@field_validator` to run custom validation logic on individual fields. Validators are classmethods that receive the value and return it (possibly transformed).

### Basic Validation

```python
import re
from pydantic import BaseModel, field_validator

VALID_NAME_REGEX = re.compile(r"^[a-zA-Z]{2,}$")

class User(BaseModel):
    name: str
    email: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not VALID_NAME_REGEX.match(v):
            raise ValueError("Name must contain only letters and be at least 2 characters")
        return v
```

### mode="before" — Pre-Validation Transform

Runs before Pydantic's built-in type validation. Use for type coercion or normalization.

```python
import enum
from pydantic import BaseModel, field_validator

class Role(enum.IntFlag):
    Author = 1
    Editor = 2
    Admin = 4

class User(BaseModel):
    role: Role

    @field_validator("role", mode="before")
    @classmethod
    def validate_role(cls, v: int | str | Role) -> Role:
        """Accept int, string name, or Role enum."""
        converters = {
            int: lambda x: Role(x),
            str: lambda x: Role[x],
            Role: lambda x: x,
        }
        try:
            return converters[type(v)](v)
        except (KeyError, ValueError):
            raise ValueError(f"Invalid role. Use one of: {', '.join(r.name for r in Role)}")
```

### Validating Multiple Fields with One Validator

```python
class Address(BaseModel):
    city: str
    country: str
    postcode: str

    @field_validator("city", "country")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Must not be empty")
        return v.strip()
```

---

## 3. Model Validators

Use `@model_validator` for cross-field validation — when the validity of one field depends on another.

### mode="before" — Pre-Validation

Receives raw input data (dict) before any field validation. Use for cross-field checks on raw data or data transformation.

```python
from typing import Any
from pydantic import BaseModel, model_validator

class User(BaseModel):
    name: str
    password: str

    @model_validator(mode="before")
    @classmethod
    def validate_user(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "name" in data and "password" in data:
            if data["name"].casefold() in data["password"].casefold():
                raise ValueError("Password cannot contain username")
        return data
```

### mode="after" — Post-Validation

Receives the fully constructed model instance. Use for business rule validation where you need typed, validated fields.

```python
from typing import Self
from pydantic import BaseModel, model_validator

class DateRange(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_date_order(self) -> Self:
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self
```

### When to Use Before vs After

| mode="before" | mode="after" |
|---|---|
| Raw dict input, fields not yet validated | Fully typed model instance |
| Data transformation (hashing, normalization) | Business rules (date range, cross-field logic) |
| Missing field checks before Pydantic errors | Access to computed defaults |
| Can modify the raw data and return it | Returns `Self` |

---

## 4. Serializers

Control how model data is exported via `model_dump()` and `model_dump(mode="json")`.

### Field Serializer

```python
from pydantic import BaseModel, field_serializer
from uuid import UUID

class User(BaseModel):
    id: UUID
    role: Role

    @field_serializer("id", when_used="json")
    def serialize_id(self, id: UUID) -> str:
        return str(id)

    @field_serializer("role", when_used="json")
    @classmethod
    def serialize_role(cls, v: Role) -> str:
        return v.name
```

### Model Serializer

```python
from pydantic import BaseModel, model_serializer

class User(BaseModel):
    name: str
    role: Role
    password: SecretStr

    @model_serializer(mode="wrap", when_used="json")
    def serialize_user(self, serializer, info) -> dict[str, Any]:
        # Custom JSON shape — omit password, flatten role
        if not info.include and not info.exclude:
            return {"name": self.name, "role": self.role.name}
        return serializer(self)
```

### when_used Options

| Value | Applies to |
|---|---|
| `"always"` | Both `model_dump()` and `model_dump(mode="json")` |
| `"json"` | Only `model_dump(mode="json")` |
| `"unless-none"` | Skips serialization when value is None |

---

## 5. Model Configuration

### ConfigDict

```python
from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    model_config = ConfigDict(
        extra="forbid",          # reject unknown fields (raises ValidationError)
        frozen=True,             # immutable instances (hashable)
        from_attributes=True,    # enable ORM mode (read from SQLAlchemy objects)
        str_strip_whitespace=True,  # strip whitespace from all str fields
    )
    name: str
    email: str
```

### Common Config Options

| Option | Effect |
|---|---|
| `extra="forbid"` | Reject fields not in the model (prevents typos) |
| `extra="allow"` | Store unknown fields in `__pydantic_extra__` |
| `frozen=True` | All fields immutable, instances hashable |
| `from_attributes=True` | Create model from ORM objects via attribute access |
| `str_strip_whitespace=True` | Auto-strip all string fields |
| `validate_default=True` | Validate default values too |

### Settings from Environment Variables

```python
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./db.sqlite3"
    api_key: str = ""
    log_level: str = "INFO"

    model_config = ConfigDict(env_file=".env")
```

---

## 6. Special Types

Pydantic provides validated types that replace raw str/int for common patterns:

```python
from pydantic import BaseModel, EmailStr, SecretStr, UUID4, HttpUrl, PositiveInt, PositiveFloat

class User(BaseModel):
    email: EmailStr                  # validates email format
    password: SecretStr              # hidden in repr/str, access via .get_secret_value()
    id: UUID4                        # validates UUID v4
    website: HttpUrl                 # validates URL format
    age: PositiveInt                 # must be > 0
    balance: PositiveFloat           # must be > 0.0
```

> `EmailStr` requires `pip install pydantic[email]` (uses the `email-validator` package).

### Decimal for Currency and Financial Data

Never use `float` for money — floating-point arithmetic causes rounding errors (`0.1 + 0.2 != 0.3`). Use `Decimal` with explicit precision:

```python
from decimal import Decimal
from pydantic import BaseModel, Field

class Invoice(BaseModel):
    amount: Decimal = Field(ge=0, decimal_places=2)
    tax_rate: Decimal = Field(ge=0, le=1, decimal_places=4)

    @property
    def total(self) -> Decimal:
        return (self.amount * (1 + self.tax_rate)).quantize(Decimal("0.01"))
```

Alternatively, use **integer cents** (as shown throughout this plugin's examples) — `price: int` where 100 means $1.00. This avoids floating-point entirely and simplifies arithmetic. The cents approach is Arjan's preferred convention.

---

## 7. Patterns for the Three-Layer Architecture

### Create vs Read Models with Validation

```python
class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return v.strip().title()

class Customer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
```

### Partial Update Models

```python
class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip().title()
        return v
```

Use `data.model_dump(exclude_none=True)` in the operations layer to only update provided fields.

### Validation Errors in FastAPI

FastAPI automatically returns 422 Unprocessable Entity when Pydantic validation fails. The response body includes detailed error information. No extra error handling needed for input validation.

```python
# This automatically validates and returns 422 on bad input
@router.post("/customers", response_model=Customer)
async def create_customer(data: CustomerCreate):
    return customer_ops.create_customer(data, db_interface)
```

---

## 8. Anti-Patterns

| Anti-Pattern | Why it hurts | Do this instead |
|---|---|---|
| Validating in the router | Business rules leak into HTTP layer | Put validation in Pydantic models or operations |
| Raw dict everywhere | No validation, no type safety | Define Pydantic models per entity |
| One model for create + read | Exposes internal fields (id) on create | Separate `Create` and `Read` models |
| Validating fields individually with if-statements | Scattered validation, no reuse | Use `@field_validator` on the model |
| Not using `mode="before"` for type coercion | Pydantic errors on valid-but-wrong-type input | Transform in a before validator |
