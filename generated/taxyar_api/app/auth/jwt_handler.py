# app/auth/jwt_handler.py
"""
JWT handler — تولید و تأیید توکن
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.config import settings


# ═══════════════════════════════════════════════════════════
# تولید توکن
# ═══════════════════════════════════════════════════════════
def create_access_token(user_id: int, extra: Optional[dict] = None) -> str:
    """تولید JWT access token"""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra:
        payload.update(extra)

    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


# ═══════════════════════════════════════════════════════════
# تأیید توکن
# ═══════════════════════════════════════════════════════════
def decode_token(token: str) -> Optional[dict]:
    """
    Decode و verify یه JWT.
    اگه معتبر باشه dict برمی‌گردونه، وگرنه None.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def get_user_id_from_token(token: str) -> Optional[int]:
    """user_id رو از token استخراج می‌کنه"""
    payload = decode_token(token)
    if not payload:
        return None
    sub = payload.get("sub")
    if sub is None:
        return None
    try:
        return int(sub)
    except (ValueError, TypeError):
        return None


# ═══════════════════════════════════════════════════════════
# محاسبه زمان انقضا (ثانیه)
# ═══════════════════════════════════════════════════════════
def get_token_expire_seconds() -> int:
    return settings.JWT_EXPIRE_MINUTES * 60