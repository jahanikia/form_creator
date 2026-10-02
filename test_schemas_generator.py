# test_routers_generator.py
"""
تست تولید routers/*.py + database.py + config.py
"""

import os
from src.services.schema_store import SchemaStore
from src.services.routers_generator import RoutersGenerator


def _copy_template(template_path: str, output_path: str) -> bool:
    """کپی یه template به مسیر خروجی"""
    if not os.path.exists(template_path):
        print(f"   ⚠️  template نبود: {template_path}")
        return False
    with open(template_path, "r", encoding="utf-8") as f:
        code = f.read()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"   ✅ {output_path}")
    return True


def main():
    print("🔍 اتصال به SQLite...")
    store = SchemaStore()

    project = store.get_active_project()
    print(f"📦 پروژه: {project.name} ({project.fa_name})")

    tables = store.list_tables(project.id)
    print(f"📋 {len(tables)} جدول\n")

    # ═══ مسیرهای خروجی ═══
    base_dir = os.path.join("generated", f"{project.name}_api", "app")
    routers_dir = os.path.join(base_dir, "routers")
    auth_dir = os.path.join(base_dir, "auth")
    templates_dir = os.path.join("src", "services", "templates")

    os.makedirs(routers_dir, exist_ok=True)
    os.makedirs(auth_dir, exist_ok=True)

    # ═══ 1. config.py ═══
    print("📝 ساخت config.py...")
    _copy_template(
        os.path.join(templates_dir, "app_config.py"),
        os.path.join(base_dir, "config.py"),
    )

    # ═══ 2. auth/password.py ═══
    print("\n🔐 ساخت auth/password.py...")
    _copy_template(
        os.path.join(templates_dir, "auth_password.py"),
        os.path.join(auth_dir, "password.py"),
    )

    # ═══ 3. database.py ═══
    print("\n🗄️  ساخت database.py...")
    _copy_template(
        os.path.join(templates_dir, "app_database.py"),
        os.path.join(base_dir, "database.py"),
    )

    # ═══ 4. routers ═══
    print("\n🐍 تولید routers/*.py...")
    gen = RoutersGenerator(project, tables)
    files = gen.generate_all()

    total_lines = 0
    for table_name, code in files.items():
        path = os.path.join(routers_dir, f"{table_name}.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        lines = code.count("\n")
        total_lines += lines
        print(f"   ✅ {table_name}.py ({lines} خط)")

    # ═══ 5. __init__.py ها ═══
    print("\n📦 ساخت __init__.py ها...")
    for pkg_dir in [base_dir, routers_dir, auth_dir]:
        init_path = os.path.join(pkg_dir, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w", encoding="utf-8") as f:
                f.write("")
            print(f"   ✅ {init_path}")

    print(f"\n📊 مجموع: {len(files)} router، {total_lines} خط")
    print(f"📁 مسیر: {os.path.abspath(routers_dir)}")


if __name__ == "__main__":
    main()