#   app/api/v1/routes_auth.py
from fastapi import APIRouter, Depends, HTTPException, Request, status, Body
from sqlalchemy.orm import Session

from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import UserCreate, UserLogin, Token, UserOut
from app.db.pg import get_db
from app.repos.user_repo import create_user, get_user_by_email
from app.core.security import decode_token, verify_password, create_access_token, create_refresh_token, get_raw_token
from app.core.auth import get_current_user, get_current_active_user, get_current_superuser
from app.db.mongo import blacklist_token, store_otp, verify_otp
from app.core.email import send_email

router = APIRouter()

@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = await create_user(db, email=user.email, password=user.password)
    return new_user

@router.post("/login", response_model=Token)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(str(db_user.id))
    refresh_token = create_refresh_token(str(db_user.id))
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    token = get_raw_token(request)            
    payload = decode_token(token) 
    if not payload:
        raise HTTPException(401, "Invalid token")
    await blacklist_token(payload["jti"], expires_in=3600)
    return {"msg": "Logged out"}

@router.post("/refresh", response_model=Token)
async def refresh(token: str = Body(...)):
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid refresh token")

    # revoke old refresh token
    await blacklist_token(payload["jti"], expires_in=86400)

    user_id = payload["sub"]
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

# -------- Password Reset (request OTP) --------
@router.post("/password-reset/request")
async def password_reset_request(email: str = Body(...)):
    import random
    otp = str(random.randint(100000, 999999))
    await store_otp(email, otp)
    send_email(email, "Password Reset OTP", f"Your OTP is: {otp}")
    return {"msg": "OTP sent to email"}

# -------- Password Reset (verify OTP) --------
@router.post("/password-reset/verify")
async def password_reset_verify(email: str = Body(...), otp: str = Body(...), new_password: str = Body(...), db: AsyncSession = Depends(get_db)):
    if not await verify_otp(email, otp):
        raise HTTPException(400, "Invalid or expired OTP")
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(404, "User not found")
    from app.core.security import hash_password
    user.hashed_password = hash_password(new_password)
    db.add(user)
    await db.commit()
    return {"msg": "Password reset successful"}

# -------- Superuser-only route --------
@router.get("/superuser", response_model=UserOut)
async def superuser_route(current_user = Depends(get_current_superuser)):
    return current_user
