import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MemberStatus
from app.models import PlatformMember, User

logger = logging.getLogger(__name__)


async def link_platform_member(db: AsyncSession, user: User) -> None:
    """Connect a signed-in user to their platform member row, found by email.

    Called during sign-in, after Google has confirmed the email. The caller
    commits, so the link is saved together with the user and the session.
    """
    email = user.email.strip().lower()
    member = await db.scalar(
        select(PlatformMember).where(PlatformMember.email == email)
    )

    if member is None:
        return
    if member.status == MemberStatus.DISABLED:
        return
    if member.user_id is not None and member.user_id != user.id:
        logger.warning(
            "Platform member %s is already linked to another user", member.email
        )
        return

    member.user_id = user.id
    member.status = MemberStatus.ACTIVE
