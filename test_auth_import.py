# test_auth_import.py
import sys
from pathlib import Path

generated_dir = Path(__file__).parent / "generated" / "taxyar_api"
sys.path.insert(0, str(generated_dir))

print("🔍 تست import auth...\n")

try:
    from app.auth.jwt_handler import create_access_token, decode_token
    from app.auth.dependencies import get_current_user
    from app.routers import auth

    print("✅ همه importها موفق!\n")

    # ─── تست JWT ───
    token = create_access_token(user_id=42)
    print(f"🔑 token ساخته شد: {token[:50]}...")

    payload = decode_token(token)
    print(f"📦 payload: {payload}")

    assert payload["sub"] == "42", "user_id اشتباهه"
    print("✅ decode درست کار می‌کنه\n")

    # ─── endpointهای auth ───
    print("📋 endpointهای auth:")
    for r in auth.router.routes:
        methods = ",".join(sorted(r.methods))
        print(f"   [{methods:10}] {r.path}")

    print("\n🎉 همه چیز خوبه!")

except Exception as e:
    print(f"\n❌ خطا: {type(e).__name__}: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)