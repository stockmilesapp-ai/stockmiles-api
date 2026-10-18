"""Permission guards. They check permissions held in the database, never role
names, so changes made on the roles screen take effect at once (D61).

AND: list several guards, `dependencies=[CanA, CanB]`; FastAPI runs them all.
OR: `require_any("a.b.c", "x.y.z")`.
"""

from fastapi import HTTPException, status

from app.api.guards.auth import CurrentUser
from app.db.session import DbSession
from app.models import User
from app.services.access import get_platform_access


def require_permission(key: str):
    """Let the request through only if the user holds `key`."""
    return require_any(key)


def require_any(*keys: str):
    """Let the request through if the user holds at least one of `keys`."""

    async def check(user: CurrentUser, db: DbSession) -> User:
        access = await get_platform_access(db, user)
        if not any(key in access.permissions for key in keys):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed")
        return user

    return check
