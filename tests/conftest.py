import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.session import SessionLocal
from app.main import app
from app.models import User


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
