import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.cache import cache_manager
from app.database.base import Base
from app.database.session import get_db
from app.main import app
from tests.utils import create_test_token

# Устанавливаем тестовое окружение
os.environ["TESTING"] = "True"

# Тестовая база данных PostgreSQL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://test_user:test_password@localhost:5433/test_crm_db"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    await wait_for_db()

    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )

    # Создаем все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture
def client(test_engine) -> Generator[TestClient, None, None]:
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_redis.keys = AsyncMock(return_value=[])

    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with async_session() as session:
            try:
                yield session
            finally:
                await session.close()

    # Mock для cache_manager
    with patch.object(cache_manager, "get_redis", return_value=mock_redis):
        app.dependency_overrides[get_db] = override_get_db

        with TestClient(app) as test_client:
            yield test_client

        app.dependency_overrides.clear()


async def wait_for_db():
    import asyncpg

    for i in range(30):
        try:
            conn = await asyncpg.connect(
                "postgresql://test_user:test_password@localhost:5433/test_crm_db"
            )
            await conn.close()
            print("✅ Test database is ready!")
            break
        except Exception as e:
            if i == 29:
                print(f"❌ Database connection failed after 30 attempts: {e}")
                raise
            print(f"⏳ Waiting for test database... ({i + 1}/30)")
            await asyncio.sleep(2)


@pytest.fixture
def sample_user_data():
    return {"email": "test@example.com", "password": "Pass123", "name": "Test User"}


@pytest.fixture
def sample_organization_data():
    return {"name": "Test Organization"}


@pytest.fixture
def sample_contact_data():
    return {"name": "Test Contact", "email": "contact@example.com", "phone": "+1234567890"}


@pytest.fixture
def sample_deal_data():
    return {
        "title": "Test Deal",
        "amount": 1000.0,
        "currency": "USD",
        "status": "new",
        "stage": "qualification",
        "description": "Test deal description",
    }


@pytest.fixture(autouse=True)
def setup_test_data():
    """Синхронная фикстура для настройки тестовых данных"""
    # Просто устанавливаем глобальные переменные, без асинхронных операций
    pytest.test_token = create_test_token(user_id=1)
    pytest.test_organization_id = 1
    pytest.test_headers = {
        "Authorization": f"Bearer {pytest.test_token}",
        "X-Organization-Id": str(pytest.test_organization_id),
    }
