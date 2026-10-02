# test_schemas_import.py
"""
تست اینکه schemas.py تولیدشده توسط Pydantic لود می‌شه.
"""

import sys
from pathlib import Path

generated_dir = Path(__file__).parent / "generated" / "taxyar_api"
sys.path.insert(0, str(generated_dir))

print("🔍 تلاش برای import کردن schemas.py...\n")

try:
    from app.schemas.schemas import (
        UserBase, UserCreate, UserUpdate, UserResponse,
        UserProfileBase, UserProfileCreate, UserProfileUpdate, UserProfileResponse,
        RoleBase, RoleCreate, RoleUpdate, RoleResponse,
    )
    print("✅ import موفق بود!\n")

    # ─── تست UserCreate ───
    print("🧪 تست UserCreate:")
    u = UserCreate(
        first_name="علی",
        last_name="رضایی",
        user_name="ali",
        email="ali@example.com",
        password="secret123",
    )
    print(f"   ✅ ساخته شد: {u.user_name} / {u.email}")
    print(f"   🔒 password (tوی model): {u.password[:3]}***")

    # ─── تست UserResponse (نباید password داشته باشه) ───
    print("\n🧪 تست UserResponse — چک عدم وجود password:")
    fields = UserResponse.model_fields.keys()
    if "password" in fields:
        print(f"   ❌ خطا! password توی Response هست: {list(fields)}")
    else:
        print(f"   ✅ password توی Response نیست")
        print(f"   📋 فیلدها: {list(fields)}")

    # ─── تست UserUpdate (همه Optional) ───
    print("\n🧪 تست UserUpdate (بدون هیچ فیلدی):")
    upd = UserUpdate()
    print(f"   ✅ ساخته شد بدون فیلد: {upd.model_dump(exclude_none=True)}")

    # ─── تست اعتبارسنجی ایمیل ───
    print("\n🧪 تست اعتبارسنجی ایمیل (ایمیل نامعتبر):")
    try:
        UserCreate(
            first_name="تست",
            last_name="تست",
            user_name="test",
            email="not-an-email",
            password="secret123",
        )
        print("   ❌ خطا! ایمیل نامعتبر قبول شد")
    except Exception as e:
        print(f"   ✅ ایمیل نامعتبر رد شد: {type(e).__name__}")

    # ─── بررسی فیلدهای حساس توی Response ───
    print("\n🔒 بررسی فیلدهای حساس:")
    checks = [
        ("Session", "token"),
        ("PasswordReset", "token"),
        ("JwtBlacklist", "token"),
    ]
    from app.schemas import schemas as s
    for cls_name, sensitive_field in checks:
        resp_cls = getattr(s, f"{cls_name}Response", None)
        if resp_cls is None:
            print(f"   ⚠️ {cls_name}Response پیدا نشد")
            continue
        if sensitive_field in resp_cls.model_fields:
            print(f"   ❌ {cls_name}Response شامل {sensitive_field} است")
        else:
            print(f"   ✅ {cls_name}Response بدون {sensitive_field}")

    print("\n🎉 همه چیز خوبه!")

except Exception as e:
    print(f"\n❌ خطا: {type(e).__name__}: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)