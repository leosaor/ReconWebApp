import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.validation import validate_target_value


class TargetCreate(BaseModel):
    value: Annotated[str, Field(min_length=1, max_length=255)]
    kind: Literal["domain", "ip"] = "domain"

    @field_validator("value")
    @classmethod
    def _validate_value(cls, v: str) -> str:
        try:
            return validate_target_value(v)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc


class TargetUpdate(BaseModel):
    value: Annotated[str | None, Field(min_length=1, max_length=255)] = None

    @field_validator("value")
    @classmethod
    def _validate_value(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            return validate_target_value(v)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc


class TargetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    value: str
    kind: str
    created_at: datetime
