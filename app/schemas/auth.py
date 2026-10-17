import uuid

from pydantic import BaseModel, Field

from app.schemas.base import ApiModel


class GoogleLoginRequest(BaseModel):
    credential: str


class UserOut(ApiModel):
    id: uuid.UUID
    email: str
    name: str


class PlatformRoleOut(ApiModel):
    key: str
    name: str


class CurrentUserOut(UserOut):
    platform_role: PlatformRoleOut | None = None
    permissions: list[str] = Field(default_factory=list)
