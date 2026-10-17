"""Make platform_members match platform_members.json.

Run from the stockmiles-api folder:

    uv run python -m app.seeds.load_platform_members

It targets the database in DATABASE_URL and can be run any number of times.
"""

import asyncio
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MemberStatus, PlatformRole, PlatformTenantScope
from app.db.session import SessionLocal
from app.models import PlatformMember

SEED_FILE = Path(__file__).with_name("platform_members.json")


def read_seed_file(path: Path = SEED_FILE) -> list[dict[str, Any]]:
    return json.loads(path.read_text())


async def load_platform_members(
    db: AsyncSession, entries: list[dict[str, Any]]
) -> None:
    """Insert or update every entry; disable members that are no longer listed.

    Members are disabled rather than deleted, so the access links they created
    keep their author.
    """
    emails: list[str] = []
    for entry in entries:
        email = entry["email"].strip().lower()
        member = await db.scalar(
            select(PlatformMember).where(PlatformMember.email == email)
        )
        if member is None:
            member = PlatformMember(email=email)
            db.add(member)
        # Unknown values raise ValueError, which stops the run before commit.
        member.role = PlatformRole(entry["role"])
        member.tenant_scope = PlatformTenantScope(entry["tenantScope"])
        # Becomes active once the person signs in with this email.
        member.status = (
            MemberStatus.INVITED if member.user_id is None else MemberStatus.ACTIVE
        )
        emails.append(email)

    await db.execute(
        update(PlatformMember)
        .where(PlatformMember.email.not_in(emails))
        .values(status=MemberStatus.DISABLED)
    )
    await db.commit()


async def main() -> None:
    entries = read_seed_file()
    async with SessionLocal() as db:
        await load_platform_members(db, entries)
    print(f"Platform members loaded: {len(entries)} listed in {SEED_FILE.name}")


if __name__ == "__main__":
    asyncio.run(main())
