from pydantic import BaseModel, ConfigDict


class CodeValueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    label: str
    description: str | None
    sort_order: int
    is_active: bool
