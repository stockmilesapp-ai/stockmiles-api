import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.platform_member_tenant import PlatformMemberTenant
    from app.models.role import Role


class PlatformMember(Base):
    __tablename__ = "platform_members"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    role: Mapped[str | None] = mapped_column(String(32))
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"), index=True
    )
    tenant_scope: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tenant_links: Mapped[list["PlatformMemberTenant"]] = relationship(
        back_populates="platform_member", cascade="all, delete-orphan"
    )
    role_ref: Mapped["Role | None"] = relationship()
