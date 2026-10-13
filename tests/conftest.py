import asyncio
import uuid

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import delete

from alembic import command
from app.core.settings import settings

if not settings.test_database_url:
    raise RuntimeError("TEST_DATABASE_URL is not set. Tests never run on DATABASE_URL.")
if "@localhost:" not in settings.test_database_url:
    raise RuntimeError("TEST_DATABASE_URL must point at localhost.")
settings.database_url = settings.test_database_url

from app.db.session import SessionLocal
from app.main import app
from app.models import User


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    """Build the schema in the test database once, before the first test."""
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def client():
    return TestClient(app, base_url="https://testserver")


@pytest.fixture
def google_user(monkeypatch):
    claims = {
        "sub": f"test-{uuid.uuid4()}",
        "email": "test.user@example.com",
        "email_verified": True,
        "name": "Test User",
    }
    monkeypatch.setattr("app.api.routes.auth.verify_google_token", lambda token: claims)
    yield claims

    async def remove_test_user():
        async with SessionLocal() as db:
            await db.execute(delete(User).where(User.google_sub == claims["sub"]))
            await db.commit()

    asyncio.run(remove_test_user())
