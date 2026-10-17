import asyncio

import pytest
from sqlalchemy import delete, select, update

from app.core.enums import MemberStatus
from app.db.session import SessionLocal
from app.models import PlatformMember, Role

OWNER_PERMISSIONS = [
    "platform.access_links.create",
    "platform.metadata.manage",
    "platform.metadata.read",
    "platform.roles.manage",
    "platform.roles.read",
    "platform.tenants.manage",
    "platform.tenants.read",
]


def _add_member(email: str, role_key: str) -> None:
    async def run():
        async with SessionLocal() as db:
            role = await db.scalar(
                select(Role).where(Role.tenant_id.is_(None), Role.key == role_key)
            )
            assert role is not None
            db.add(
                PlatformMember(
                    email=email,
                    role_id=role.id,
                    role=role.key,
                    tenant_scope="all",
                    status=MemberStatus.INVITED,
                )
            )
            await db.commit()

    asyncio.run(run())


def _disable_member(email: str) -> None:
    async def run():
        async with SessionLocal() as db:
            await db.execute(
                update(PlatformMember)
                .where(PlatformMember.email == email)
                .values(status=MemberStatus.DISABLED)
            )
            await db.commit()

    asyncio.run(run())


@pytest.fixture(autouse=True)
def clean_platform_members():
    async def wipe():
        async with SessionLocal() as db:
            await db.execute(delete(PlatformMember))
            await db.commit()

    asyncio.run(wipe())
    yield
    asyncio.run(wipe())


def _me(client) -> dict:
    """Sign in (which links the platform member) and return /auth/me."""
    assert client.post("/auth/google", json={"credential": "any"}).status_code == 200
    response = client.get("/auth/me")
    assert response.status_code == 200
    return response.json()


def test_owner_gets_the_owner_role_and_every_platform_permission(client, google_user):
    _add_member(google_user["email"], "platform_owner")
    me = _me(client)
    assert me["platformRole"] == {"key": "platform_owner", "name": "Platform owner"}
    assert me["permissions"] == OWNER_PERMISSIONS


def test_admin_can_view_roles_but_not_change_them(client, google_user):
    _add_member(google_user["email"], "platform_admin")
    me = _me(client)
    assert me["platformRole"]["key"] == "platform_admin"
    assert "platform.roles.read" in me["permissions"]
    assert "platform.roles.manage" not in me["permissions"]
    assert len(me["permissions"]) == 6


def test_a_user_who_is_not_a_member_has_no_platform_access(client, google_user):
    me = _me(client)
    assert me["email"] == google_user["email"]
    assert me["platformRole"] is None
    assert me["permissions"] == []


def test_a_disabled_member_loses_access_even_when_linked(client, google_user):
    _add_member(google_user["email"], "platform_owner")
    assert _me(client)["platformRole"] is not None
    _disable_member(google_user["email"])
    me = client.get("/auth/me").json()
    assert me["platformRole"] is None
    assert me["permissions"] == []


def test_json_keys_are_camel_case(client, google_user):
    me = _me(client)
    assert set(me) == {"id", "email", "name", "platformRole", "permissions"}
