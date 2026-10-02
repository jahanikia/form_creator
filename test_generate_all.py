# test_generate_all.py
"""
تولید کامل پروژه‌ی FastAPI:
  models + schemas + routers + auth + main + config + database
"""

import os
import shutil
from src.services.schema_store import SchemaStore
from src.services.python_generator import PythonGenerator
from src.services.schemas_generator import SchemasGenerator
from src.services.routers_generator import RoutersGenerator


def _copy_template(template_path: str, output_path: str) -> bool:
    if not os.path.exists(template_path):
        print(f"   ⚠️  template نبود: {template_path}")
        return False
    with open(template_path, "r", encoding="utf-8") as f:
        code = f.read()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"   ✅ {output_path}")
    return True


def _write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    # ═══ پاک کردن generated قبلی ═══
    if os.path.exists("generated"):
        print("🗑  پاک کردن generated قبلی...")
        shutil.rmtree("generated", ignore_errors=True)

    print("🔍 اتصال به SQLite...")
    store = SchemaStore()
    project = store.get_active_project()
    print(f"📦 پروژه: {project.name} ({project.fa_name})")

    tables = store.list_tables(project.id)
    groups = store.list_groups(project.id)
    print(f"📋 {len(tables)} جدول، {len(groups)} گروه\n")

    project_root = os.path.join("generated", f"{project.name}_api")
    base_dir = os.path.join(project_root, "app")
    models_dir = os.path.join(base_dir, "models")
    schemas_dir = os.path.join(base_dir, "schemas")
    routers_dir = os.path.join(base_dir, "routers")
    auth_dir = os.path.join(base_dir, "auth")
    templates_dir = os.path.join("src", "services", "templates")

    for d in [base_dir, models_dir, schemas_dir, routers_dir, auth_dir]:
        os.makedirs(d, exist_ok=True)

    # ═══════════════════════════════════════════════════
    # 1. models
    # ═══════════════════════════════════════════════════
    print("🐍 [1/8] models/models.py...")
    gen = PythonGenerator(project, tables, groups)
    _write_file(os.path.join(models_dir, "models.py"), gen.generate_models())
    print(f"   ✅ models/models.py")

    # ═══════════════════════════════════════════════════
    # 2. schemas
    # ═══════════════════════════════════════════════════
    print("\n📋 [2/8] schemas/schemas.py...")
    gen = SchemasGenerator(project, tables)
    _write_file(os.path.join(schemas_dir, "schemas.py"), gen.generate_schemas())
    print(f"   ✅ schemas/schemas.py")

    # ═══════════════════════════════════════════════════
    # 3. routers (جدول‌ها)
    # ═══════════════════════════════════════════════════
    print("\n🌐 [3/8] routers/*.py...")
    gen = RoutersGenerator(project, tables)
    files = gen.generate_all()
    for table_name, code in files.items():
        _write_file(os.path.join(routers_dir, f"{table_name}.py"), code)
        print(f"   ✅ {table_name}.py")

    # ═══════════════════════════════════════════════════
    # 4. auth (jwt + dependencies)
    # ═══════════════════════════════════════════════════
    print("\n🔐 [4/8] auth/...")
    _copy_template(
        os.path.join(templates_dir, "auth_password.py"),
        os.path.join(auth_dir, "password.py"),
    )
    _copy_template(
        os.path.join(templates_dir, "auth_jwt_handler.py"),
        os.path.join(auth_dir, "jwt_handler.py"),
    )
    _copy_template(
        os.path.join(templates_dir, "auth_dependencies.py"),
        os.path.join(auth_dir, "dependencies.py"),
    )

    # ═══════════════════════════════════════════════════
    # 5. auth router
    # ═══════════════════════════════════════════════════
    print("\n🔐 [5/8] routers/auth.py...")
    _copy_template(
        os.path.join(templates_dir, "auth_router.py"),
        os.path.join(routers_dir, "auth.py"),
    )

    # ═══════════════════════════════════════════════════
    # 6. config + database + main
    # ═══════════════════════════════════════════════════
    print("\n⚙️  [6/8] config.py + database.py + main.py...")
    _copy_template(
        os.path.join(templates_dir, "app_config.py"),
        os.path.join(base_dir, "config.py"),
    )
    _copy_template(
        os.path.join(templates_dir, "app_database.py"),
        os.path.join(base_dir, "database.py"),
    )
    _copy_template(
        os.path.join(templates_dir, "app_main.py"),
        os.path.join(base_dir, "main.py"),
    )

    # ═══════════════════════════════════════════════════
    # 7. فایل‌های ریشه
    # ═══════════════════════════════════════════════════
    print("\n📦 [7/8] .env.example + requirements.txt + README.md...")
    _copy_template(
        os.path.join(templates_dir, "env_example.txt"),
        os.path.join(project_root, ".env.example"),
    )
    _copy_template(
        os.path.join(templates_dir, "app_requirements.txt"),
        os.path.join(project_root, "requirements.txt"),
    )
    _copy_template(
        os.path.join(templates_dir, "app_readme.md"),
        os.path.join(project_root, "README.md"),
    )

    # ═══════════════════════════════════════════════════
    # 8. __init__.py ها
    # ═══════════════════════════════════════════════════
    print("\n📁 [8/8] __init__.py ها...")
    for pkg_dir in [base_dir, models_dir, schemas_dir, routers_dir, auth_dir]:
        init_path = os.path.join(pkg_dir, "__init__.py")
        if not os.path.exists(init_path):
            _write_file(init_path, "")
            print(f"   ✅ {init_path}")

    print(f"\n🎉 پروژه کامل شد!")
    print(f"📁 {os.path.abspath(project_root)}")


if __name__ == "__main__":
    main()