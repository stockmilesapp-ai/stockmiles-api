import asyncio

import pytest
from sqlalchemy import delete, select

from app.core.enums import MemberStatus
from app.db.session import SessionLocal
from app.models import PlatformMember, Role, Tenant

TENANT_NAMES = ["Zeta Traders", "Alpha Stores"]


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


@pytest.fixture(autouse=True)
def tenants_and_clean_members():
    async def add_tenants():
        async with SessionLocal() as db:
            for name in TENANT_NAMES:
                db.add(
                    Tenant(
                        name=name,
                        tenant_type="chain",
                        template_key="clothing",
                        country_code="IN",
                        currency_code="INR",
                    )
                )
            await db.commit()

    async def wipe():
        async with SessionLocal() as db:
            await db.execute(delete(PlatformMember))
            await db.execute(delete(Tenant).where(Tenant.name.in_(TENANT_NAMES)))
            await db.commit()

    asyncio.run(wipe())
    asyncio.run(add_tenants())
    yield
    asyncio.run(wipe())


def _sign_in(client) -> None:
    assert client.post("/auth/google", json={"credential": "any"}).status_code == 200


def test_requires_sign_in(client):
    assert client.get("/platform/tenants").status_code == 401


def test_a_user_without_platform_access_is_refused(client, google_user):
    _sign_in(client)
    assert client.get("/platform/tenants").status_code == 403


@pytest.mark.parametrize(
    "role_key", ["platform_owner", "platform_admin", "platform_support"]
)
def test_platform_members_see_every_tenant_by_name(client, google_user, role_key):
    _add_member(google_user["email"], role_key)
    _sign_in(client)
    response = client.get("/platform/tenants")
    assert response.status_code == 200
    names = [t["name"] for t in response.json() if t["name"] in TENANT_NAMES]
    assert names == sorted(TENANT_NAMES)


def test_json_is_camel_case_and_only_listed_fields(client, google_user):
    _add_member(google_user["email"], "platform_owner")
    _sign_in(client)
    tenant = client.get("/platform/tenants").json()[0]
    assert set(tenant) == {
        "id",
        "name",
        "tenantType",
        "templateKey",
        "countryCode",
        "currencyCode",
        "status",
        "createdAt",
    }
    assert tenant["status"] == "draft"
