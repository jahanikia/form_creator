# app/auth/password.py
"""
Password hashing با passlib + bcrypt
"""

from passlib.context import CryptContext


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(plain: str) -> str:
    """هش کردن پسورد"""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """بررسی پسورد"""
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False