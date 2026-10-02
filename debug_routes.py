# debug_routes.py
import sys
from pathlib import Path

generated_dir = Path(__file__).parent / "generated" / "taxyar_api"
sys.path.insert(0, str(generated_dir))

print("=" * 60)
print("📁 DIAGNOSTIC")
print("=" * 60)

# ═══════════════════════════════════════════════
# 1. چک: مسیرها
# ═══════════════════════════════════════════════
print(f"\n[1] sys.path[0]: {sys.path[0]}")
print(f"[1] generated_dir: {generated_dir}")
print(f"[1] generated_dir exists: {generated_dir.exists()}")

# ═══════════════════════════════════════════════
# 2. چک: فایل‌ها
# ═══════════════════════════════════════════════
print("\n[2] چک فایل‌های کلیدی:")
files = [
    "app/__init__.py",
    "app/main.py",
    "app/config.py",
    "app/database.py",
    "app/models/models.py",
    "app/schemas/schemas.py",
    "app/routers/__init__.py",
    "app/routers/users.py",
    "app/auth/password.py",
]
for f in files:
    p = generated_dir / f
    status = "✅" if p.exists() else "❌"
    print(f"   {status} {f}")

# ═══════════════════════════════════════════════
# 3. چک: import گام‌به‌گام
# ═══════════════════════════════════════════════
print("\n[3] import گام‌به‌گام:")

# 3a. app
try:
    import app
    print(f"   ✅ import app → {app.__file__}")
except Exception as e:
    print(f"   ❌ import app: {type(e).__name__}: {e}")
    sys.exit(1)

# 3b. app.config
try:
    from app.config import settings
    print(f"   ✅ app.config → APP_NAME={settings.APP_NAME}")
except Exception as e:
    print(f"   ❌ app.config: {type(e).__name__}: {e}")
    sys.exit(1)

# 3c. app.models
try:
    from app.models import models
    print(f"   ✅ app.models → {len(models.Base.metadata.tables)} جدول")
except Exception as e:
    print(f"   ❌ app.models: {type(e).__name__}: {e}")
    sys.exit(1)

# 3d. app.schemas
try:
    from app.schemas import schemas
    print(f"   ✅ app.schemas → {len(schemas.__all__)} کلاس")
except Exception as e:
    print(f"   ❌ app.schemas: {type(e).__name__}: {e}")
    sys.exit(1)

# 3e. app.auth.password
try:
    from app.auth import password
    print(f"   ✅ app.auth.password")
except Exception as e:
    print(f"   ❌ app.auth.password: {type(e).__name__}: {e}")
    sys.exit(1)

# 3f. app.database
try:
    from app.database import engine, get_db, SessionLocal
    print(f"   ✅ app.database → engine={engine.url.drivername}")
except Exception as e:
    print(f"   ❌ app.database: {type(e).__name__}: {e}")
    sys.exit(1)

# 3g. app.routers.users
try:
    from app.routers import users
    print(f"   ✅ app.routers.users → {len(users.router.routes)} route")
    for r in users.router.routes:
        print(f"        {sorted(r.methods)} {r.path}")
except Exception as e:
    print(f"   ❌ app.routers.users: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ═══════════════════════════════════════════════
# 4. حالا main
# ═══════════════════════════════════════════════
print("\n[4] import main:")

try:
    from app import main
    print(f"   ✅ import app.main → {main.__file__}")
    print(f"   📊 main.app type: {type(main.app)}")
    print(f"   📊 main.app.routes count: {len(main.app.routes)}")
    print(f"\n   همه‌ی routeها:")
    for r in main.app.routes:
        if hasattr(r, "methods"):
            print(f"      {sorted(r.methods)} {r.path}")
except Exception as e:
    print(f"   ❌ app.main: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ═══════════════════════════════════════════════
# 5. چک نهایی: include_router در سورس
# ═══════════════════════════════════════════════
print("\n[5] چک سورس main.py:")
import inspect
src = inspect.getsource(main)
print(f"   تعداد 'include_router' در سورس: {src.count('include_router')}")

print("\n" + "=" * 60)