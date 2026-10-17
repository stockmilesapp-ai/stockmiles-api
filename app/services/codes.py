from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from app.models import Code, CodeValue


def _codes_with_shared_values() -> Select[tuple[Code]]:
    # One query: LEFT JOIN keeps codes that have no values yet, and the
    # tenant filter sits in the ON clause so it narrows values, not codes.
    # Only shared values (no tenant) for now; a tenant's own values join in
    # once requests carry the current member.
    return (
        select(Code)
        .outerjoin(Code.values.and_(CodeValue.tenant_id.is_(None)))
        .options(contains_eager(Code.values))
        .order_by(Code.key, CodeValue.sort_order, CodeValue.label)
    )


async def list_codes(db: AsyncSession) -> list[Code]:
    result = await db.scalars(_codes_with_shared_values())
    return list(result.unique())


async def get_code(db: AsyncSession, key: str) -> Code | None:
    result = await db.scalars(_codes_with_shared_values().where(Code.key == key))
    return result.unique().one_or_none()
