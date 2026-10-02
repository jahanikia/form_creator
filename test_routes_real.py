# test_routes_real.py
"""
تست واقعی routeها با TestClient (نه شمردن app.routes)
"""

import sys
from pathlib import Path

generated_dir = Path(__file__).parent / "generated" / "taxyar_api"
sys.path.insert(0, str(generated_dir))

print("=" * 70)
print("🔍 تست واقعی endpointها با TestClient")
print("=" * 70)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ═══════════════════════════════════════════════
# 1. چک: OpenAPI schema (همه‌ی routeها توش هستن)
# ═══════════════════════════════════════════════
print("\n[1] تعداد endpointها از OpenAPI:")
r = client.get("/openapi.json")
schema = r.json()
paths = schema.get("paths", {})
print(f"    📊 {len(paths)} مسیر یکتا در OpenAPI:")
for path in sorted(paths.keys()):
    methods = ", ".join(paths[path].keys())
    print(f"       [{methods:25}] {path}")

# ═══════════════════════════════════════════════
# 2. چک: هر endpoint واقعاً جواب می‌ده
# ═══════════════════════════════════════════════
print("\n[2] تست چند endpoint (بدون DB):")
print("    (این تست‌ها به DB وصل نمی‌شن — فقط چک می‌کنن route وجود داره)")

# root
r = client.get("/")
print(f"    GET /              → {r.status_code}")

# health
r = client.get("/health")
print(f"    GET /health        → {r.status_code}")

# users (بدون DB → خطای 500 می‌ده، ولی یعنی route وجود داره)
endpoints_to_test = [
    "/users/count",
    "/users",
    "/user_profiles/count",
    "/roles/count",
    "/permissions/count",
    "/user_roles/count",
    "/role_permissions/count",
    "/sessions/count",
    "/password_resets/count",
    "/otp_codes/count",
    "/login_attempts/count",
    "/user_activities/count",
    "/jwt_blacklist/count",
]

print()
for ep in endpoints_to_test:
    r = client.get(ep)
    status_icon = "✅" if r.status_code != 404 else "❌"
    print(f"    {status_icon} GET {ep:30} → {r.status_code}")

print("\n🎉 تست تمام شد!")
print("\n📌 نکته: هر status != 404 یعنی route وجود داره.")
print("   status 500 یعنی route هست ولی DB وصل نیست (طبیعیه).")