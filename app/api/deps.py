from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_token
from app.core.settings import settings
from app.db.session import get_db
from app.models import User, UserSession

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(request: Request, db: DbSession) -> User:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")

    result = await db.execute(
        select(User)
        .join(UserSession, UserSession.user_id == User.id)
        .where(
            UserSession.token_hash == hash_token(token),
            UserSession.expires_at > datetime.now(UTC),
        )
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def check_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin is not None and origin not in settings.allowed_origins:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Origin not allowed")
