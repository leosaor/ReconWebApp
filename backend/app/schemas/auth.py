import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None


class LoginRequest(BaseModel):
    identifier: str | None = Field(default=None, min_length=1)
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=1)
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ApiKeyCreated(BaseModel):
    id: uuid.UUID
    name: str
    prefix: str
    raw_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    prefix: str
    revoked: bool
    last_used_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
