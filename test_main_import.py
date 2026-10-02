# test_main_import.py
"""تست import کردن main.py و بررسی همه‌ی endpointها (روش OpenAPI)"""

import sys
from pathlib import Path

generated_dir = Path(__file__).parent / "generated" / "taxyar_api"
sys.path.insert(0, str(generated_dir))

print("🔍 تلاش برای import کردن main.py...\n")

try:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    print("✅ app با موفقیت لود شد!\n")

    # ─── از OpenAPI بشمار (روش جدید FastAPI) ───
    r = client.get("/openapi.json")
    paths = r.json().get("paths", {})

    print(f"📋 {len(paths)} مسیر یکتا:\n")
    for path in sorted(paths.keys()):
        methods = ",".join(sorted(paths[path].keys()))
        print(f"   [{methods:20}] {path}")

    print("\n🎉 همه چیز خوبه!")

except Exception as e:
    print(f"\n❌ خطا: {type(e).__name__}: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)