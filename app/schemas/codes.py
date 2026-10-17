import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import ApiModel


class CodeValueOut(ApiModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    key: str
    label: str
    description: str | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CodeOut(ApiModel):
    id: uuid.UUID
    key: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    # The model calls the relationship `values`; the API calls it `codeValues`.
    code_values: list[CodeValueOut] = Field(
        validation_alias="values", serialization_alias="codeValues"
    )
