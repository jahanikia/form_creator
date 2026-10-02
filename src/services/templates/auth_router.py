# app/routers/auth.py
"""
Auth router — register / login / me / logout
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session as DBSession

from app.auth.dependencies import get_current_user, get_current_user_with_token
from app.auth.jwt_handler import (
    create_access_token,
    get_token_expire_seconds,
)
from app.auth.password import hash_password, verify_password
from app.database import get_db
from app.models.models import User, JwtBlacklist
from app.schemas.schemas import UserCreate, UserResponse


router = APIRouter(prefix="/auth", tags=["auth"])


# ═══════════════════════════════════════════════════════════
# Schemas محلی
# ═══════════════════════════════════════════════════════════
class LoginRequest(BaseModel):
    identifier: str = Field(..., description="username / email / mobile")
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class MessageResponse(BaseModel):
    detail: str


# ═══════════════════════════════════════════════════════════
# POST /auth/register
# ═══════════════════════════════════════════════════════════
@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: UserCreate, db: DBSession = Depends(get_db)):
    """ثبت‌نام کاربر جدید + برگرداندن توکن"""

    existing = db.scalar(
        select(User).where(
            or_(
                User.user_name == payload.user_name,
                User.email == payload.email,
            )
        ).limit(1)
    )
    if existing:
        if existing.user_name == payload.user_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="این نام کاربری قبلاً ثبت شده",
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="این ایمیل قبلاً ثبت شده",
        )

    data = payload.model_dump()
    data["password"] = hash_password(data["password"])

    user = User(**data)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        expires_in=get_token_expire_seconds(),
        user=UserResponse.model_validate(user),
    )


# ═══════════════════════════════════════════════════════════
# POST /auth/login
# ═══════════════════════════════════════════════════════════
@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DBSession = Depends(get_db)):
    """ورود با identifier (username/email/mobile) + password"""

    user = db.scalar(
        select(User).where(
            or_(
                User.user_name == payload.identifier,
                User.email == payload.identifier,
                User.mobile == payload.identifier,
            )
        ).limit(1)
    )

    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور اشتباه است",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حساب کاربری غیرفعال است",
        )

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        expires_in=get_token_expire_seconds(),
        user=UserResponse.model_validate(user),
    )


# ═══════════════════════════════════════════════════════════
# GET /auth/me
# ═══════════════════════════════════════════════════════════
@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """اطلاعات کاربر فعلی"""
    return current_user


# ═══════════════════════════════════════════════════════════
# POST /auth/logout
# ═══════════════════════════════════════════════════════════
@router.post("/logout", response_model=MessageResponse)
def logout(
    user_token: tuple[User, str] = Depends(get_current_user_with_token),
    db: DBSession = Depends(get_db),
):
    """خروج — توکن فعلی رو به blacklist اضافه می‌کنه"""
    current_user, token = user_token

    # ─── چک: قبلاً blacklist شده؟ ───
    existing = db.scalar(
        select(JwtBlacklist).where(JwtBlacklist.token == token).limit(1)
    )
    if existing:
        return MessageResponse(detail="قبلاً خارج شده بودید")

    # ─── اضافه به blacklist ───
    # (expires_at → از token استخراج می‌کنیم)
    from app.auth.jwt_handler import decode_token
    payload = decode_token(token) or {}
    exp = payload.get("exp")
    expires_at = (
        datetime.fromtimestamp(exp, tz=timezone.utc) if exp else None
    )

    bl = JwtBlacklist(
        token=token,
        user_id=current_user.id,
        expires_at=expires_at,
    )
    db.add(bl)
    db.commit()

    return MessageResponse(detail="با موفقیت خارج شدید")