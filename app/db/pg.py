# app/db/pg.py
from __future__ import annotations
import asyncio
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.exc import OperationalError
from sqlalchemy.engine import URL
from tenacity import retry, wait_exponential, stop_after_delay, retry_if_exception_type
from sqlalchemy import text

from app.core.config import settings

logger = logging.getLogger(__name__)

# Build async DB URL (asyncpg)
POSTGRES_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD,
    host=settings.POSTGRES_HOST,
    port=settings.POSTGRES_PORT,
    database=settings.POSTGRES_DB,
)

# Recommended production-ish engine options
# pool_size not supported by asyncpg driver in the same way; tuning via poolclass and max_overflow is advanced.
engine = create_async_engine(
    POSTGRES_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_timeout=30,            # seconds
    connect_args={"server_settings": {"application_name": settings.PROJECT_NAME}},
)

# async_sessionmaker (SQLAlchemy 2.0)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# Retry on connection failure during startup (exponential backoff)
@retry(
    reraise=True,
    wait=wait_exponential(multiplier=1, min=1, max=30),
    stop=stop_after_delay(60),
    retry=retry_if_exception_type(OperationalError),
)
async def wait_for_postgres():
    """
    Try to establish a simple connection — useful in container startup ordering.
    Tenacity handles retries with exponential backoff.
    """
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))  # <- FIXED
    logger.info("Postgres available")

# Dependency for fastapi endpoints
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for endpoints. Yields an async session and ensures rollback on exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # commit is handled by repositories / services where appropriate
        except Exception:
            await session.rollback()
            raise

# Helper to close engine on shutdown
async def close_engine():
    await engine.dispose()
