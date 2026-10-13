import asyncio

from sqlalchemy import select

from app.core.enums import SYSTEM_CODES
from app.db.session import SessionLocal
from app.models import Code, CodeValue


def _system_values() -> dict[str, dict[str, bool]]:
    async def load():
        async with SessionLocal() as db:
            result = await db.execute(
                select(Code.key, CodeValue.key, CodeValue.is_active)
                .join(CodeValue, CodeValue.code_id == Code.id)
                .where(Code.is_system.is_(True), CodeValue.tenant_id.is_(None))
            )
            return result.all()

    values: dict[str, dict[str, bool]] = {}
    for code_key, value_key, is_active in asyncio.run(load()):
        values.setdefault(code_key, {})[value_key] = is_active
    return values


def test_system_codes_match_enums():
    values = _system_values()
    assert set(values) == set(SYSTEM_CODES)
    for code_key, enum in SYSTEM_CODES.items():
        assert set(values[code_key]) == {member.value for member in enum}, code_key


def test_franchise_is_seeded_inactive():
    tenant_types = _system_values()["tenant_type"]
    assert tenant_types == {"individual": True, "chain": True, "franchise": False}
