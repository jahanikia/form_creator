# app/database.py
"""
اتصال به MySQL با SQLAlchemy 2.0
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.models import Base


# ═══════════════════════════════════════════════════════════
# Engine
# ═══════════════════════════════════════════════════════════
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
    future=True,
)


# ═══════════════════════════════════════════════════════════
# Session
# ═══════════════════════════════════════════════════════════
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# ═══════════════════════════════════════════════════════════
# Dependency برای FastAPI
# ═══════════════════════════════════════════════════════════
def get_db():
    """Dependency: یه session SQLAlchemy می‌ده و بعد می‌بنده"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = ["engine", "SessionLocal", "get_db", "Base"]