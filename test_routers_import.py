# test_routers_import.py
"""
تست اینکه routerهای تولیدشده قابل import هستن.
"""

import sys
from pathlib import Path

generated_dir = Path(__file__).parent / "generated" / "taxyar_api"
sys.path.insert(0, str(generated_dir))

print("🔍 تلاش برای import کردن routerها...\n")

try:
    from app.routers import (
        users, roles, permissions, sessions,
        user_profiles, user_roles, role_permissions,
        password_resets, otp_codes, login_attempts,
        user_activities, jwt_blacklist,
    )
    print("✅ همه‌ی routerها import شدن!\n")

    # ─── endpointهای users ───
    print("📋 endpointهای users:")
    for route in users.router.routes:
        methods = ",".join(sorted(route.methods))
        print(f"   [{methods:8}] {route.path}")

    # ─── endpointهای user_roles (junction) ───
    print("\n📋 endpointهای user_roles (junction):")
    for route in user_roles.router.routes:
        methods = ",".join(sorted(route.methods))
        print(f"   [{methods:8}] {route.path}")

    # ─── چک: junction نباید PATCH داشته باشه ───
    ur_methods = set()
    for route in user_roles.router.routes:
        ur_methods.update(route.methods)

    if "PATCH" in ur_methods:
        print("\n   ❌ خطا! user_roles نباید PATCH داشته باشه")
    else:
        print("\n   ✅ user_roles بدون PATCH")

    # ─── چک: users باید PATCH داشته باشه ───
    u_methods = set()
    for route in users.router.routes:
        u_methods.update(route.methods)

    if "PATCH" in u_methods:
        print("   ✅ users دارای PATCH")
    else:
        print("   ❌ users باید PATCH داشته باشه!")

    print("\n🎉 همه چیز خوبه!")

except Exception as e:
    print(f"\n❌ خطا: {type(e).__name__}: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)