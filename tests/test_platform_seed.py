import asyncio
import uuid

import pytest
from sqlalchemy import delete, select

from app.core.enums import MemberStatus
from app.db.session import SessionLocal
from app.models import PlatformMember
from app.seeds.load_platform_members import load_platform_members, read_seed_file


def _entry(email: str, role: str = "platform_admin", scope: str = "all"):
    return {"email": email, "role": role, "tenantScope": scope}


def _load(entries):
    async def run():
        async with SessionLocal() as db:
            await load_platform_members(db, entries)

    asyncio.run(run())


def _members() -> dict[str, PlatformMember]:
    async def run():
        async with SessionLocal() as db:
            rows = await db.scalars(select(PlatformMember))
            return {member.email: member for member in rows}

    return asyncio.run(run())


@pytest.fixture(autouse=True)
def clean_platform_members():
    async def wipe():
        async with SessionLocal() as db:
            await db.execute(delete(PlatformMember))
            await db.commit()

    asyncio.run(wipe())
    yield
    asyncio.run(wipe())


def test_seed_file_is_valid():
    entries = read_seed_file()
    assert entries, "platform_members.json must list at least one member"
    _load(entries)
    assert len(_members()) == len(entries)


def test_loading_twice_keeps_one_row_per_email():
    email = f"admin-{uuid.uuid4()}@example.com"
    _load([_entry(email)])
    _load([_entry(email)])
    members = _members()
    assert list(members) == [email]
    assert members[email].status == MemberStatus.INVITED


def test_emails_are_stored_trimmed_and_lowercase():
    _load([_entry("  Admin@Example.COM ")])
    assert list(_members()) == ["admin@example.com"]


def test_members_left_out_of_the_file_are_disabled_not_deleted():
    kept, removed = "kept@example.com", "removed@example.com"
    _load([_entry(kept), _entry(removed)])
    _load([_entry(kept)])
    members = _members()
    assert members[kept].status == MemberStatus.INVITED
    assert members[removed].status == MemberStatus.DISABLED


def test_a_disabled_member_listed_again_comes_back():
    email = "back@example.com"
    _load([_entry(email)])
    _load([])
    assert _members()[email].status == MemberStatus.DISABLED
    _load([_entry(email)])
    assert _members()[email].status == MemberStatus.INVITED


def test_unknown_role_stops_the_load():
    with pytest.raises(ValueError):
        _load([_entry("bad@example.com", role="super_admin")])
    assert _members() == {}
