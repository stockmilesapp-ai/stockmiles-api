import asyncio
import uuid

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.core.enums import MemberStatus
from app.db.session import SessionLocal
from app.models import PlatformMember
from app.seeds.load_platform_members import load_platform_members, read_seed_file

OWNER = "owner@example.com"


def _entry(email: str, role: str = "platform_admin", scope: str = "all"):
    return {"email": email, "role": role, "tenantScope": scope}


def _load(entries, with_owner: bool = True):
    """Load the entries; every valid file has exactly one owner, so add one."""
    if with_owner:
        entries = [_entry(OWNER, role="platform_owner"), *entries]

    async def run():
        async with SessionLocal() as db:
            await load_platform_members(db, entries)

    asyncio.run(run())


def _members() -> dict[str, PlatformMember]:
    """Every platform member except the owner that _load adds."""

    async def run():
        async with SessionLocal() as db:
            rows = await db.scalars(
                select(PlatformMember).options(selectinload(PlatformMember.role_ref))
            )
            return {member.email: member for member in rows if member.email != OWNER}

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
    _load(entries, with_owner=False)
    members = _members()
    assert len(members) == len(entries)
    for entry in entries:
        role = members[entry["email"]].role_ref
        assert role is not None
        assert role.key == entry["role"]


def test_loading_twice_keeps_one_row_per_email():
    email = f"admin-{uuid.uuid4()}@example.com"
    _load([_entry(email)])
    _load([_entry(email)])
    members = _members()
    assert list(members) == [email]
    assert members[email].status == MemberStatus.INVITED


def test_role_id_points_at_the_listed_role():
    _load([_entry("support@example.com", role="platform_support")])
    member = _members()["support@example.com"]
    assert member.role_ref is not None
    assert member.role_ref.key == "platform_support"
    assert member.role == "platform_support"


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


@pytest.mark.parametrize("role", ["super_admin", "owner"])
def test_unknown_or_tenant_role_stops_the_load(role):
    with pytest.raises(ValueError, match="Unknown platform role"):
        _load([_entry("bad@example.com", role=role)])
    assert _members() == {}


def test_a_file_without_an_owner_stops_the_load():
    with pytest.raises(ValueError, match="exactly one platform_owner"):
        _load([_entry("admin@example.com")], with_owner=False)
    assert _members() == {}


def test_a_file_with_two_owners_stops_the_load():
    with pytest.raises(ValueError, match="exactly one platform_owner"):
        _load([_entry("second@example.com", role="platform_owner")])
    assert _members() == {}
