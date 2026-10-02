# test_models_import.py
"""
تست اینکه models.py تولیدشده واقعاً توسط SQLAlchemy لود می‌شه.
"""

import sys
from pathlib import Path

# اضافه کردن مسیر پروژه‌ی تولیدشده به sys.path
generated_dir = Path(__file__).parent / "generated" / "taxyar_api"
sys.path.insert(0, str(generated_dir))

print("🔍 تلاش برای import کردن models.py...\n")

try:
    from app.models.models import (
        Base, User, UserProfile, Role, Permission,
        UserRole, RolePermission, Session, PasswordReset,
        OtpCode, LoginAttempt, UserActivity, JwtBlacklist,
    )
    print("✅ import موفق بود!\n")

    # ─── تعداد جداول ───
    tables = Base.metadata.tables
    print(f"📋 {len(tables)} جدول در metadata:")
    for name in sorted(tables.keys()):
        print(f"   • {name}")

    # ─── بررسی relationshipهای User ───
    print(f"\n🔗 relationshipهای User:")
    mapper = User.__mapper__
    for rel in mapper.relationships:
        target = rel.mapper.class_.__name__
        direction = "→" if rel.direction.name == "MANYTOONE" else "←"
        print(f"   {direction} {rel.key} → {target}")

    # ─── بررسی FKهای UserProfile ───
    print(f"\n🔑 FKهای UserProfile:")
    for fk in UserProfile.__table__.foreign_keys:
        print(f"   • {fk.parent.name} → {fk.target_fullname}")

    print("\n🎉 همه چیز خوبه!")

except Exception as e:
    print(f"\n❌ خطا: {type(e).__name__}: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)