# app/repos/user_repo.py
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User
from app.core.security import hash_password

async def create_user(session: AsyncSession, email: str, password: str, is_superuser: bool = False) -> User:
    user = User(email=email, hashed_password=hash_password(password), is_superuser=is_superuser)
    session.add(user)
    await session.flush()
    await session.commit()
    await session.refresh(user)
    return user

async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
    return await session.get(User, user_id)

async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    q = select(User).where(User.email == email)
    res = await session.execute(q)
    return res.scalar_one_or_none()

async def list_users(session: AsyncSession, limit: int = 50, offset: int = 0):
    q = select(User).limit(limit).offset(offset)
    res = await session.execute(q)
    return res.scalars().all()

async def update_user(session: AsyncSession, user: User, *, email: str | None = None, password: str | None = None, is_active: bool | None = None):
    if email is not None:
        user.email = email
    if password is not None:
        user.hashed_password = hash_password(password)
    if is_active is not None:
        user.is_active = is_active
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def delete_user(session: AsyncSession, user: User):
    await session.delete(user)
    await session.commit()
    return
