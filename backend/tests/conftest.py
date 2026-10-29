import asyncio
import os
import shutil
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.main import app

# Use isolated SQLite database for tests
TEST_DB_FILE = "./test_screening.db"
TEST_STORAGE_DIR = "./test_storage"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def init_test_db():
    # Setup test storage dir
    os.makedirs(TEST_STORAGE_DIR, exist_ok=True)
    settings.STORAGE_DIR = TEST_STORAGE_DIR

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Seed test users
    async with TestAsyncSessionLocal() as session:
        officer = User(
            username="officer",
            email="officer@demo.com",
            hashed_password=get_password_hash("OfficerSecure2026!"),
            role="officer",
            is_active=True
        )
        admin = User(
            username="admin",
            email="admin@demo.com",
            hashed_password=get_password_hash("AdminSecure2026!"),
            role="admin",
            is_active=True
        )
        session.add(officer)
        session.add(admin)
        await session.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Cleanup storage
    if os.path.exists(TEST_STORAGE_DIR):
        shutil.rmtree(TEST_STORAGE_DIR, ignore_errors=True)
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def officer_token(client: AsyncClient) -> str:
    res = await client.post("/api/v1/auth/login", json={
        "username": "officer",
        "password": "OfficerSecure2026!"
    })
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient) -> str:
    res = await client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "AdminSecure2026!"
    })
    assert res.status_code == 200
    return res.json()["access_token"]

