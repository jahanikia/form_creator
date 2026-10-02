# debug_step_by_step.py
import sys
from pathlib import Path

generated_dir = Path(__file__).parent / "generated" / "taxyar_api"
sys.path.insert(0, str(generated_dir))

print("=" * 70)
print("🔍 تست دستی include_router")
print("=" * 70)

# ═══════════════════════════════════════════════
# 1. اول FastAPI app رو خالی بساز (مثل main.py)
# ═══════════════════════════════════════════════
from fastapi import FastAPI
from app.config import settings

app = FastAPI(title=settings.APP_NAME)
print(f"\n[1] app خالی ساخته شد → {len(app.routes)} route")

# ═══════════════════════════════════════════════
# 2. root و health رو اضافه کن (مثل main.py)
# ═══════════════════════════════════════════════
@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}

print(f"[2] بعد از root+health → {len(app.routes)} route")

# ═══════════════════════════════════════════════
# 3. حالا users.router رو include کن
# ═══════════════════════════════════════════════
from app.routers import users
print(f"\n[3] users.router → {len(users.router.routes)} route")
print(f"    users.router.routes type: {type(users.router.routes)}")

before = len(app.routes)
app.include_router(users.router)
after = len(app.routes)
print(f"[3] قبل از include: {before}, بعد از include: {after} (+{after-before})")

# ═══════════════════════════════════════════════
# 4. حالا همه رو include کن
# ═══════════════════════════════════════════════
from app.routers import (
    user_profiles, roles, permissions, user_roles,
    role_permissions, sessions, password_resets,
    otp_codes, login_attempts, user_activities, jwt_blacklist,
)

routers = [
    ("user_profiles", user_profiles),
    ("roles", roles),
    ("permissions", permissions),
    ("user_roles", user_roles),
    ("role_permissions", role_permissions),
    ("sessions", sessions),
    ("password_resets", password_resets),
    ("otp_codes", otp_codes),
    ("login_attempts", login_attempts),
    ("user_activities", user_activities),
    ("jwt_blacklist", jwt_blacklist),
]

for name, mod in routers:
    before = len(app.routes)
    app.include_router(mod.router)
    after = len(app.routes)
    print(f"    + {name}.router: +{after-before} → کل {after}")

print(f"\n[4] کل routeها: {len(app.routes)}")

# ═══════════════════════════════════════════════
# 5. حالا از main.py import کن (مقایسه)
# ═══════════════════════════════════════════════
from app import main as main_module
print(f"\n[5] main.app.routes: {len(main_module.app.routes)}")
print(f"[5] app.routes (دستی): {len(app.routes)}")

# ═══════════════════════════════════════════════
# 6. چک: چرا این‌قدر فرق داره؟
# ═══════════════════════════════════════════════
print(f"\n[6] مقایسه:")
print(f"    main.py routes: {[r.path for r in main_module.app.routes]}")