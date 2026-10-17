import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, false, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.role_permission import RolePermission


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (
        # System roles have no tenant; without NULLS NOT DISTINCT Postgres would
        # accept two system roles with the same key.
        UniqueConstraint(
            "tenant_id",
            "key",
            name="uq_roles_tenant_key",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    scope: Mapped[str] = mapped_column(String(16))
    kind: Mapped[str | None] = mapped_column(String(16))
    key: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(500))
    level: Mapped[int] = mapped_column()
    store_access: Mapped[str | None] = mapped_column(String(16))
    app_access: Mapped[bool] = mapped_column(default=True, server_default=true())
    is_system: Mapped[bool] = mapped_column(default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    permission_links: Mapped[list["RolePermission"]] = relationship(
        back_populates="role", cascade="all, delete-orphan"
    )
