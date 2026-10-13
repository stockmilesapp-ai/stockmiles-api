import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.platform_member import PlatformMember


class PlatformMemberTenant(Base):
    __tablename__ = "platform_member_tenants"
    __table_args__ = (
        UniqueConstraint(
            "platform_member_id",
            "tenant_id",
            name="uq_platform_member_tenants_member_tenant",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    platform_member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("platform_members.id", ondelete="CASCADE"), index=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    platform_member: Mapped["PlatformMember"] = relationship(
        back_populates="tenant_links"
    )
