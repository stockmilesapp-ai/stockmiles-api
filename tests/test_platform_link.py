import asyncio
import uuid

import pytest
from sqlalchemy import delete, select

from app.core.enums import MemberStatus
from app.db.session import SessionLocal
from app.models import PlatformMember, Role, User


def _add_member(email: str, status: MemberStatus = MemberStatus.INVITED) -> None:
    async def run():
        async with SessionLocal() as db:
            role = await db.scalar(
                select(Role).where(
                    Role.tenant_id.is_(None), Role.key == "platform_admin"
                )
            )
            assert role is not None
            db.add(
                PlatformMember(
                    email=email,
                    role_id=role.id,
                    role=role.key,
                    tenant_scope="all",
                    status=status,
                )
            )
            await db.commit()

    asyncio.run(run())


def _member(email: str) -> PlatformMember | None:
    async def run():
        async with SessionLocal() as db:
            return await db.scalar(
                select(PlatformMember).where(PlatformMember.email == email)
            )

    return asyncio.run(run())


def _user_id(google_sub: str) -> uuid.UUID | None:
    async def run():
        async with SessionLocal() as db:
            return await db.scalar(select(User.id).where(User.google_sub == google_sub))

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


def _sign_in(client):
    response = client.post("/auth/google", json={"credential": "any"})
    assert response.status_code == 200


def test_sign_in_links_an_invited_member(client, google_user):
    _add_member(google_user["email"])
    _sign_in(client)
    member = _member(google_user["email"])
    assert member is not None
    assert member.status == MemberStatus.ACTIVE
    assert member.user_id == _user_id(google_user["sub"])


def test_email_case_and_spaces_do_not_matter(client, google_user):
    _add_member(google_user["email"])
    google_user["email"] = f"  {google_user['email'].upper()} "
    _sign_in(client)
    member = _member(google_user["email"].strip().lower())
    assert member is not None
    assert member.status == MemberStatus.ACTIVE


def test_signing_in_twice_keeps_the_link(client, google_user):
    _add_member(google_user["email"])
    _sign_in(client)
    _sign_in(client)
    member = _member(google_user["email"])
    assert member is not None
    assert member.user_id == _user_id(google_user["sub"])


def test_a_disabled_member_is_not_linked(client, google_user):
    _add_member(google_user["email"], status=MemberStatus.DISABLED)
    _sign_in(client)
    member = _member(google_user["email"])
    assert member is not None
    assert member.status == MemberStatus.DISABLED
    assert member.user_id is None


def test_a_member_linked_to_another_user_is_left_alone(client, google_user):
    _add_member(google_user["email"])
    _sign_in(client)
    first_user = _user_id(google_user["sub"])

    # Same email, different Google account.
    google_user["sub"] = f"test-{uuid.uuid4()}"
    _sign_in(client)
    member = _member(google_user["email"])
    assert member is not None
    assert member.user_id == first_user

    async def remove_second_user():
        async with SessionLocal() as db:
            await db.execute(delete(User).where(User.google_sub == google_user["sub"]))
            await db.commit()

    asyncio.run(remove_second_user())


def test_unverified_email_never_links(client, google_user):
    _add_member(google_user["email"])
    google_user["email_verified"] = False
    response = client.post("/auth/google", json={"credential": "any"})
    assert response.status_code == 401
    member = _member(google_user["email"])
    assert member is not None
    assert member.user_id is None


def test_a_user_who_is_not_a_member_signs_in_as_before(client, google_user):
    _sign_in(client)
    assert _member(google_user["email"]) is None
