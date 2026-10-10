from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import delete, select

from app.api.deps import CurrentUser, DbSession, check_origin
from app.core.security import hash_token, new_session_token
from app.core.settings import settings
from app.models import User, UserSession
from app.schemas.auth import GoogleLoginRequest, UserOut
from app.services.google import verify_google_token

router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[Depends(check_origin)])


@router.post("/google", response_model=UserOut)
async def sign_in_with_google(
    body: GoogleLoginRequest, response: Response, db: DbSession
) -> User:
    try:
        claims = await run_in_threadpool(verify_google_token, body.credential)
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid Google token"
        ) from exc
    if not claims.get("email_verified"):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Google email is not verified"
        )

    result = await db.execute(select(User).where(User.google_sub == claims["sub"]))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(google_sub=claims["sub"])
        db.add(user)
    user.email = claims["email"]
    user.name = claims.get("name", "")
    await db.flush()

    token = new_session_token()
    max_age = settings.session_days * 24 * 60 * 60
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=datetime.now(UTC) + timedelta(seconds=max_age),
        )
    )
    await db.commit()

    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return user


@router.get("/me", response_model=UserOut)
async def read_me(user: CurrentUser) -> User:
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def sign_out(request: Request, response: Response, db: DbSession) -> None:
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        await db.execute(
            delete(UserSession).where(UserSession.token_hash == hash_token(token))
        )
        await db.commit()
    response.delete_cookie(key=settings.session_cookie_name, path="/")
