# app/db/mongo.py
from __future__ import annotations
import logging
from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from datetime import datetime, timedelta, timezone
from app.core.config import settings

logger = logging.getLogger(__name__)

_mongo_client: AsyncIOMotorClient | None = None

def get_mongo_client() -> AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    return _mongo_client

def get_mongo_db() -> AsyncIOMotorDatabase:
    client = get_mongo_client()
    return client[settings.MONGO_DB]

async def init_indexes():
    db = get_mongo_db()
    await db.token_blacklist.create_index("jti", unique=True)
    await db.token_blacklist.create_index("expires_at", expireAfterSeconds=0)
    await db.otps.create_index("email", unique=True)
    await db.otps.create_index("expires_at", expireAfterSeconds=0)

async def blacklist_token(jti: str, expires_in: int = 3600):
    db = get_mongo_db()
    await db.token_blacklist.insert_one({"jti": jti, "expires_at": datetime.now(timezone.utc) + timedelta(seconds=expires_in)})

async def is_token_blacklisted(jti: str) -> bool:
    db = get_mongo_db()
    return await db.token_blacklist.find_one({"jti": jti}) is not None


async def store_otp(email: str, otp: str, expires_in: int = 300):
    db = get_mongo_db()
    await db.otps.update_one(
        {"email": email},
        {"$set": {"otp": otp, "expires_at": datetime.now(timezone.utc) + timedelta(seconds=expires_in)}},
        upsert=True
    )

async def verify_otp(email: str, otp: str) -> bool:
    db = get_mongo_db()
    doc = await db.otps.find_one({"email": email})
    if not doc:
        return False

    expires_at = doc["expires_at"]
    if expires_at.tzinfo is None:  # naive datetime from Mongo
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if doc["otp"] == otp and expires_at > datetime.now(timezone.utc):
        await db.otps.delete_one({"email": email})
        return True
    return False

# FastAPI dependency
async def mongo_db_dependency() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    yield get_mongo_db()

# Clean shutdown (optional)
def close_mongo_client() -> None:
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        logger.info("Closed MongoDB client")
