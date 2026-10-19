from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tenant


async def list_tenants(db: AsyncSession) -> list[Tenant]:
    """Every tenant in the system, by name.

    Reads across all tenants, so only platform screens may call it
    (constitution Article 1, rule 4).
    """
    result = await db.scalars(select(Tenant).order_by(Tenant.name))
    return list(result)
