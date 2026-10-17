import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.store import Store
    from app.models.tenant_member import TenantMember


class StoreMember(Base):
    __tablename__ = "store_members"
    __table_args__ = (
        UniqueConstraint("store_id", "member_id", name="uq_store_members_store_member"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stores.id", ondelete="CASCADE"), index=True
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant_members.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    store: Mapped["Store"] = relationship(back_populates="members")
    member: Mapped["TenantMember"] = relationship(back_populates="store_memberships")
