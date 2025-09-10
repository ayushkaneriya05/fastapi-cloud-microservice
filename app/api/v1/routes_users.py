# app/api/v1/routes_users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.schemas.user import UserOut, UserUpdate, UserCreate
from app.repos import user_repo
from app.db.pg import get_db
from app.core.auth import get_current_active_user, get_current_superuser

router = APIRouter()

# Create user (admin-only) or allow open registration via auth endpoint
@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db), current_admin = Depends(get_current_superuser)):
    existing = await user_repo.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await user_repo.create_user(db, email=user_in.email, password=user_in.password, is_superuser=True)
    return user

# List users (admin)
@router.get("/", response_model=List[UserOut])
async def list_users(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db), current_admin = Depends(get_current_superuser)):
    return await user_repo.list_users(db, limit=limit, offset=offset)

# Me
@router.get("/me", response_model=UserOut)
async def get_me(current_user = Depends(get_current_active_user)):
    return current_user

# Update self or (admin) update others
@router.put("/me", response_model=UserOut)
async def update_me(data: UserUpdate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_active_user)):
    updated = await user_repo.update_user(db, current_user, email=data.email, password=data.password, is_active=data.is_active)
    return updated

# Delete user (admin)
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_admin = Depends(get_current_superuser)):
    user = await user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user_repo.delete_user(db, user)
    return
