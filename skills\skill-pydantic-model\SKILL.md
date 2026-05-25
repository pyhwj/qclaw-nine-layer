---
name: skill-pydantic-model
description: "Data model definition, validation, and serialization with Pydantic patterns distilled from pydantic/pydantic (20k+ stars)."
---

# Pydantic Data Model

Distilled from [pydantic/pydantic](https://github.com/pydantic/pydantic). Create robust data models with automatic validation, serialization, and type coercion.

## Quick Patterns

### Base Model
```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

class User(BaseModel):
    id: int
    name: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    role: UserRole = UserRole.VIEWER
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Optional[dict] = None

    @validator("name")
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()
```

### Settings Management
```python
from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    database_url: str
    api_key: str
    debug: bool = False
    max_connections: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

config = AppConfig()  # auto-loads from .env
```

### Nested Models & Serialization
```python
class Address(BaseModel):
    street: str
    city: str
    zip_code: str

class Customer(BaseModel):
    name: str
    address: Address
    orders: List[dict] = []

# JSON → Model
customer = Customer.model_validate_json('{"name":"Alice","address":{"street":"123 Main","city":"NYC","zip_code":"10001"}}')
# Model → dict
customer.model_dump()
# Partial update
customer.model_copy(update={"name": "Bob"})
```

## Anti-patterns
- Don't use `dict` when a nested model fits: `metadata: dict` → `metadata: MetaModel`
- Don't ignore `model_config` for global settings
- Don't catch ValidationError silently without logging