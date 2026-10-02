# app/config.py
"""
تنظیمات برنامه — خواندن از .env
"""

import os
import secrets
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# ═══════════════════════════════════════════════════════════
# JWT Secret — تولید یا خواندن
# ═══════════════════════════════════════════════════════════
SECRET_FILE = Path(".jwt_secret")


def _get_or_create_jwt_secret() -> str:
    """
    1. اگه متغیر محیطی JWT_SECRET بود → همون
    2. اگه فایل .jwt_secret بود → از فایل
    3. هیچ‌کدوم → یه secret جدید بساز و توی فایل ذخیره کن
    """
    # ─── 1. env var ───
    env_secret = os.getenv("JWT_SECRET")
    if env_secret:
        return env_secret

    # ─── 2. فایل ───
    if SECRET_FILE.exists():
        try:
            content = SECRET_FILE.read_text(encoding="utf-8").strip()
            if content:
                return content
        except Exception:
            pass  # اگه خطا خورد، برو مرحله 3

    # ─── 3. ساخت + ذخیره ───
    # 48 bytes → 64 کاراکتر base64 (خیلی امن)
    new_secret = secrets.token_urlsafe(48)

    try:
        SECRET_FILE.write_text(new_secret, encoding="utf-8")
        # ─── (اختیاری) محدود کردن دسترسی توی لینوکس ───
        try:
            os.chmod(SECRET_FILE, 0o600)
        except Exception:
            pass
    except Exception as e:
        import warnings
        warnings.warn(
            f"⚠️ نمی‌توان .jwt_secret را ذخیره کرد: {e}\n"
            f"⚠️ JWT_SECRET هر بار عوض می‌شود!",
            stacklevel=2,
        )

    return new_secret


# ═══════════════════════════════════════════════════════════
# Settings
# ═══════════════════════════════════════════════════════════
class Settings(BaseSettings):
    # ─── Database ───
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "taxyar_db"

    # ─── JWT ───
    # اگه توی .env/env نبود، از تابع بالا خونده می‌شه
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24

    # ─── App ───
    APP_NAME: str = "Taxyar API"
    DEBUG: bool = False

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# ═══════════════════════════════════════════════════════════
# Instantiate + fallback
# ═══════════════════════════════════════════════════════════
settings = Settings()

# اگه JWT_SECRET توی .env/env نبود → از تابع بالا بگیر
if not settings.JWT_SECRET:
    settings.JWT_SECRET = _get_or_create_jwt_secret()