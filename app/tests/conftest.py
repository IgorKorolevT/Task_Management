import pytest
import pytest_asyncio

from httpx import (
    ASGITransport,
    AsyncClient,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.user.auth import hash_password
from app.user.models import User


TEST_DATABASE_URL = "sqlite+aiosqlite://"


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
    )

    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all
        )

    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = (
        override_get_db
    )

    try:
        yield async_session
    finally:
        app.dependency_overrides.clear()

        async with engine.begin() as conn:
            await conn.run_sync(
                Base.metadata.drop_all
            )

        await engine.dispose()

@pytest_asyncio.fixture
async def db(test_db):
    async with test_db() as session:
        yield session

@pytest_asyncio.fixture
async def client(test_db):
    transport = ASGITransport(
        app=app,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def test_user(test_db):
    async with test_db() as session:
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password=hash_password(
                "testpass123"
            ),
            is_active=True,
        )

        session.add(user)

        await session.commit()
        await session.refresh(user)

        return user


@pytest_asyncio.fixture
async def auth_headers(client, test_user):
    response = await client.post(
        "/api/v1/users/login",
        json={
            "username": "testuser",
            "password": "testpass123",
        },
    )

    assert response.status_code == 200

    access_token = response.json()[
        "access_token"
    ]

    return {
        "Authorization": f"Bearer {access_token}"
    }