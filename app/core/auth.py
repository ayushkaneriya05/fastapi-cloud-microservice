#  app/core/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer,HTTPBearer,HTTPAuthorizationCredentials 
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.pg import get_db
from app.db.models import User
from app.repos.user_repo import get_user
from app.core.security import decode_token
from app.db.mongo import is_token_blacklisted

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
bearer_scheme = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials  = Depends(bearer_scheme), db: AsyncSession = Depends(get_db)) -> User:
    token = credentials.credentials  # ✅ extract string from object
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    jti = payload.get("jti")
    if await is_token_blacklisted(jti):
        raise HTTPException(status_code=401, detail="Token revoked")

    user_id = payload.get("sub")
    user = await get_user(db, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

async def get_current_superuser(current_user: User = Depends(get_current_active_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")
    return current_user
