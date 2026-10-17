from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Code, CodeValue


async def list_system_code_values(
    db: AsyncSession, code_key: str
) -> list[CodeValue] | None:
    code = await db.scalar(select(Code).where(Code.key == code_key))
    if code is None:
        return None

    result = await db.scalars(
        select(CodeValue)
        .where(CodeValue.code_id == code.id, CodeValue.tenant_id.is_(None))
        .order_by(CodeValue.sort_order, CodeValue.label)
    )
    return list(result)
