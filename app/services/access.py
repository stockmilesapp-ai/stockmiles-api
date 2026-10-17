from dataclasses import dataclass, field

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MemberStatus
from app.models import Permission, PlatformMember, Role, RolePermission, User


@dataclass
class PlatformAccess:
    role_key: str | None = None
    role_name: str | None = None
    permissions: list[str] = field(default_factory=list)


async def get_platform_access(db: AsyncSession, user: User) -> PlatformAccess:
    """The user's platform role and its active permissions, in one query."""
    rows = await db.execute(
        select(Role.key, Role.name, Permission.key)
        .select_from(PlatformMember)
        .join(Role, Role.id == PlatformMember.role_id)
        .outerjoin(RolePermission, RolePermission.role_id == Role.id)
        .outerjoin(
            Permission,
            and_(
                Permission.id == RolePermission.permission_id,
                Permission.is_active,
            ),
        )
        .where(
            PlatformMember.user_id == user.id,
            PlatformMember.status == MemberStatus.ACTIVE,
        )
        .order_by(Permission.key)
    )
    access = PlatformAccess()
    for role_key, role_name, permission_key in rows:
        access.role_key = role_key
        access.role_name = role_name
        if permission_key is not None:
            access.permissions.append(permission_key)
    return access
