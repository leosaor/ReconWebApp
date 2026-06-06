import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class TargetCreate(BaseModel):
    value: Annotated[str, Field(min_length=1, max_length=255)]
    kind: Literal["domain", "ip"] = "domain"


class TargetUpdate(BaseModel):
    value: Annotated[str | None, Field(min_length=1, max_length=255)] = None
    in_scope: bool | None = None


class TargetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    value: str
    kind: str
    in_scope: bool
    created_at: datetime
