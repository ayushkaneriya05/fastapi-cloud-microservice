import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.models import Base, User
from app.db.mongo import get_mongo_db
from app.db.pg import get_db
from app.main import app

# --- Event Loop Fixture (Session-Scoped) ---
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# --- PostgreSQL Fixtures ---
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """
    Create a clean database on startup and teardown for the entire test session.
    """
    engine = create_async_engine(settings.TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a transactional SQLAlchemy session that rolls back after each test.
    """
    engine = create_async_engine(settings.TEST_DATABASE_URL)
    AsyncSessionLocal = async_sessionmaker(
        bind=engine, autocommit=False, autoflush=False, expire_on_commit=False
    )
    async with AsyncSessionLocal() as session:
        await session.begin()
        yield session
        await session.rollback()

# --- MongoDB Fixtures ---
@pytest_asyncio.fixture
async def test_mongo_db() -> AsyncGenerator:
    """Provide a clean MongoDB database for each test."""
    client = AsyncIOMotorClient(settings.TEST_MONGO_URI)
    db = client.get_database(settings.MONGO_DB + "_test")
    try:
        yield db
    finally:
        await client.drop_database(db.name)
        client.close()

# --- FastAPI Test Client Fixture ---
@pytest.fixture
def client(db_session: AsyncSession, test_mongo_db: AsyncIOMotorClient) -> Generator[TestClient, None, None]:
    """
    Provide a FastAPI TestClient with overridden database dependencies.
    """
    def override_get_db():
        yield db_session
    
    def override_get_mongo_db():
        yield test_mongo_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_mongo_db] = override_get_mongo_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    del app.dependency_overrides[get_db]
    del app.dependency_overrides[get_mongo_db]

# --- User & Auth Fixtures ---
@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a standard, active test user."""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("password123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def superuser(db_session: AsyncSession) -> User:
    """Create a superuser."""
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("adminpass"),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def inactive_user(db_session: AsyncSession) -> User:
    """Create an inactive user."""
    user = User(
        email="inactive@example.com",
        hashed_password=hash_password("password123"),
        is_active=False,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Generate auth headers for a standard user."""
    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def superuser_auth_headers(superuser: User) -> dict:
    """Generate auth headers for a superuser."""
    token = create_access_token(subject=str(superuser.id))
    return {"Authorization": f"Bearer {token}"}

# --- Mocking Fixtures ---
@pytest.fixture(autouse=True)
def mock_s3_client():
    """Mock the S3 client for all tests."""
    with patch("app.core.s3.s3_client", new_callable=MagicMock) as mock:
        mock.generate_presigned_url.return_value = "https://s3.test/mock-url"
        yield mock

@pytest.fixture(autouse=True)
def mock_send_email():
    """Mock the send_email function for all tests."""
    with patch("app.core.email.send_email", new_callable=MagicMock) as mock:
        yield mock

