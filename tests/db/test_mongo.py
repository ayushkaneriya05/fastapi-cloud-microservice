# tests/db/test_mongo.py
import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import the functions you want to test
from app.db.mongo import (
    blacklist_token,
    is_token_blacklisted,
    store_otp,
    verify_otp,
)

@pytest.mark.asyncio
async def test_token_blacklisting(test_mongo_db: AsyncIOMotorDatabase):
    """
    Tests that a token can be blacklisted and correctly identified as such.
    The `test_mongo_db` fixture provides an isolated database for this test.
    """
    jti = "unique_token_id_123"
    
    # Pass the database fixture directly to the functions.
    is_blacklisted = await is_token_blacklisted(jti)
    assert is_blacklisted is False
    
    # Blacklist the token
    await blacklist_token(jti, expires_in=60)
    
    # Now, it should be blacklisted
    is_blacklisted_after = await is_token_blacklisted(jti)
    assert is_blacklisted_after is True

@pytest.mark.asyncio
async def test_store_and_verify_otp_success(test_mongo_db: AsyncIOMotorDatabase):
    """
    Tests the successful storage and verification of a one-time password (OTP).
    """
    email = "otp_user@example.com"
    otp = "654321"
    
    await store_otp(email, otp, expires_in=60)
    
    # Verification should be successful and consume the OTP
    assert await verify_otp(email, otp) is True
    
    # Trying to verify again should fail as the OTP is single-use
    assert await verify_otp(email, otp) is False

@pytest.mark.asyncio
async def test_verify_otp_failure_wrong_code(test_mongo_db: AsyncIOMotorDatabase):
    """
    Tests that OTP verification fails when an incorrect code is provided.
    """
    email = "wrong_otp@example.com"
    correct_otp = "111111"
    wrong_otp = "222222"

    await store_otp(email, correct_otp, expires_in=60)
    
    # Verification with the wrong code should fail
    assert await verify_otp(email, wrong_otp) is False

@pytest.mark.asyncio
async def test_verify_otp_failure_expired(test_mongo_db: AsyncIOMotorDatabase):
    """
    Tests that OTP verification fails if the OTP has expired.
    """
    email = "expired_otp@example.com"
    otp = "987654"
    
    # Store an OTP that expires in 1 second
    await store_otp(email, otp, expires_in=1)
    
    # Wait for more than 1 second to ensure it has expired
    await asyncio.sleep(1.1)
    
    # Verification should now fail
    assert await verify_otp(email, otp) is False