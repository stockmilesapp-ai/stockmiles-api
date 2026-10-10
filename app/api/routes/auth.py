import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DbSession, check_origin
from app.core.security import hash_token, new_session_token
from app.core.settings import settings
from app.models import User, UserSession
from app.schemas.auth import GoogleLoginRequest, UserOut
from app.services.google import verify_google_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# Where the browser is sent after the redirect sign-in: a page in the web app
# that shows a spinner, works out who signed in and routes them onward. The
# paths are relative, so they land on the web app's own origin, which is the
# only address the browser sees.
SIGN_IN_OK_URL = "/auth/callback?auth=success"
SIGN_IN_FAILED_URL = "/auth/callback?auth=failed"

# Name Google Identity Services uses for its double-submit CSRF token, both as
# a cookie on our origin and as a form field in its POST.
GOOGLE_CSRF_NAME = "g_csrf_token"


class SignInError(Exception):
    """The Google credential was not acceptable."""


async def _sign_in(db: AsyncSession, credential: str) -> tuple[User, str]:
    """Verify a Google ID token, upsert the user and open a session.

    Returns the user and the raw session token for the cookie.
    """
    try:
        claims = await run_in_threadpool(verify_google_token, credential)
    except ValueError as exc:
        raise SignInError("Invalid Google token") from exc
    if not claims.get("email_verified"):
        raise SignInError("Google email is not verified")

    result = await db.execute(select(User).where(User.google_sub == claims["sub"]))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(google_sub=claims["sub"])
        db.add(user)
    user.email = claims["email"]
    user.name = claims.get("name", "")
    await db.flush()

    token = new_session_token()
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=datetime.now(UTC) + timedelta(days=settings.session_days),
        )
    )
    await db.commit()
    return user, token


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post("/google", response_model=UserOut, dependencies=[Depends(check_origin)])
async def sign_in_with_google(
    body: GoogleLoginRequest, response: Response, db: DbSession
) -> User:
    """Sign in with an ID token sent as JSON by our own page."""
    try:
        user, token = await _sign_in(db, body.credential)
    except SignInError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    _set_session_cookie(response, token)
    return user


@router.post("/google/callback")
async def sign_in_with_google_redirect(
    request: Request,
    db: DbSession,
    credential: Annotated[str | None, Form()] = None,
    g_csrf_token: Annotated[str | None, Form()] = None,
) -> RedirectResponse:
    """Sign in after Google redirects the browser back in the same window.

    Google posts this form itself, so the Origin check cannot apply. Google's
    double-submit token takes its place: the value in the form must equal the
    value in the cookie its script set on our origin, which another site
    cannot read or set.
    """
    cookie_token = request.cookies.get(GOOGLE_CSRF_NAME)
    if (
        not credential
        or not g_csrf_token
        or not cookie_token
        or not secrets.compare_digest(cookie_token, g_csrf_token)
    ):
        logger.warning(
            "Google redirect sign-in rejected: credential=%s form_token=%s cookie=%s",
            bool(credential),
            bool(g_csrf_token),
            bool(cookie_token),
        )
        return RedirectResponse(SIGN_IN_FAILED_URL, status.HTTP_303_SEE_OTHER)

    try:
        _, token = await _sign_in(db, credential)
    except SignInError as exc:
        logger.warning("Google redirect sign-in rejected: %s", exc)
        return RedirectResponse(SIGN_IN_FAILED_URL, status.HTTP_303_SEE_OTHER)

    response = RedirectResponse(SIGN_IN_OK_URL, status.HTTP_303_SEE_OTHER)
    _set_session_cookie(response, token)
    return response


@router.get("/me", response_model=UserOut)
async def read_me(user: CurrentUser) -> User:
    return user


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_origin)],
)
async def sign_out(request: Request, response: Response, db: DbSession) -> None:
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        await db.execute(
            delete(UserSession).where(UserSession.token_hash == hash_token(token))
        )
        await db.commit()
    response.delete_cookie(key=settings.session_cookie_name, path="/")
