# app/auth/dependencies.py
"""
Dependencies برای FastAPI — استخراج کاربر فعلی از JWT
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.auth.jwt_handler import decode_token, get_user_id_from_token
from app.database import get_db
from app.models.models import User, JwtBlacklist


# ═══════════════════════════════════════════════════════════
# OAuth2 scheme
# ═══════════════════════════════════════════════════════════
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# ═══════════════════════════════════════════════════════════
# چک: blacklist
# ═══════════════════════════════════════════════════════════
def _is_blacklisted(db: DBSession, token: str) -> bool:
    stmt = select(JwtBlacklist).where(JwtBlacklist.token == token).limit(1)
    return db.scalar(stmt) is not None


# ═══════════════════════════════════════════════════════════
# Dependency: کاربر فعلی (اجباری)
# ═══════════════════════════════════════════════════════════
def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: DBSession = Depends(get_db),
) -> User:
    """کاربر فعلی رو برمی‌گردونه"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="توکن نامعتبر یا منقضی شده",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    if _is_blacklisted(db, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توکن باطل شده (logout)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حساب کاربری غیرفعال است",
        )

    return user


# ═══════════════════════════════════════════════════════════
# ⭐ جدید: کاربر فعلی + token
# ═══════════════════════════════════════════════════════════
def get_current_user_with_token(
    token: Optional[str] = Depends(oauth2_scheme),
    db: DBSession = Depends(get_db),
) -> tuple[User, str]:
    """
    برمی‌گردونه: (user, token)
    برای logout لازمه — token رو می‌خوایم توی blacklist بذاریم.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="توکن نامعتبر یا منقضی شده",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    if _is_blacklisted(db, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توکن باطل شده (logout)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حساب کاربری غیرفعال است",
        )

    return user, token


# ═══════════════════════════════════════════════════════════
# کاربر فعلی (اختیاری)
# ═══════════════════════════════════════════════════════════
def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: DBSession = Depends(get_db),
) -> Optional[User]:
    """مثل get_current_user ولی به‌جای خطا، None برمی‌گردونه"""
    if not token:
        return None
    try:
        return get_current_user(token=token, db=db)
    except HTTPException:
        return None