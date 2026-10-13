import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import TenantStatus
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.store import Store
    from app.models.tenant_member import TenantMember


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    tenant_type: Mapped[str] = mapped_column(String(32))
    template_key: Mapped[str] = mapped_column(String(64))
    country_code: Mapped[str] = mapped_column(String(2))
    currency_code: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(
        String(32), default=TenantStatus.DRAFT, server_default=TenantStatus.DRAFT.value
    )
    primary_contact_member_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "tenant_members.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_tenants_primary_contact_member",
        )
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    members: Mapped[list["TenantMember"]] = relationship(
        back_populates="tenant",
        foreign_keys="TenantMember.tenant_id",
        cascade="all, delete-orphan",
    )
    stores: Mapped[list["Store"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
