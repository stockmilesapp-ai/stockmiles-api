import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, UniqueConstraint, func, text, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.role_permission import RolePermission


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = (UniqueConstraint("key", name="uq_permissions_key"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(128))
    scope: Mapped[str] = mapped_column(String(16))
    module: Mapped[str] = mapped_column(String(32))
    section: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    role_links: Mapped[list["RolePermission"]] = relationship(
        back_populates="permission"
    )
