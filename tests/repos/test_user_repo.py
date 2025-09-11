# tests/repos/test_user_repo.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.repos import user_repo
from app.db.models import User

# All tests in this file should be marked with @pytest.mark.asyncio
# because they directly call asynchronous repository functions.

@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    """
    Tests that a user can be created successfully within a transaction.
    """
    email = "newuser@example.com"
    password = "strongpassword"
    user = await user_repo.create_user(db_session, email=email, password=password)
    
    # Assertions to verify the user was created correctly in the session
    assert user.email == email
    assert user.id is not None
    assert user.is_superuser is False

@pytest.mark.asyncio
async def test_get_user_by_email(db_session: AsyncSession, test_user: User):
    """
    Tests retrieving a user by their email using a pre-made user fixture.
    """
    retrieved_user = await user_repo.get_user_by_email(db_session, email=test_user.email)
    
    assert retrieved_user is not None
    assert retrieved_user.email == test_user.email

@pytest.mark.asyncio
async def test_update_user(db_session: AsyncSession, test_user: User):
    """
    Tests updating a user's details.
    """
    new_email = "updated@example.com"
    updated_user = await user_repo.update_user(db_session, user=test_user, email=new_email)
    
    assert updated_user.email == new_email

@pytest.mark.asyncio
async def test_get_user(db_session: AsyncSession, test_user: User):
    """
    Tests retrieving a user by their ID.
    """
    retrieved_user = await user_repo.get_user(db_session, user_id=test_user.id)
    
    assert retrieved_user is not None
    assert retrieved_user.id == test_user.id
    assert retrieved_user.email == test_user.email

@pytest.mark.asyncio
async def test_list_users(db_session: AsyncSession, test_user: User, superuser: User):
    """
    Tests listing all users. Note: The superuser fixture is also needed here
    to ensure it's created for the test.
    """
    users = await user_repo.list_users(db_session)
    
    # The session will contain at least the two users from the fixtures
    assert len(users) >= 2

@pytest.mark.asyncio
async def test_delete_user(db_session: AsyncSession, test_user: User):
    """
    Tests that a user can be deleted from the database.
    """
    await user_repo.delete_user(db_session, user=test_user)
    
    # Verify the user is gone by trying to fetch them again
    deleted_user = await user_repo.get_user(db_session, user_id=test_user.id)
    assert deleted_user is None