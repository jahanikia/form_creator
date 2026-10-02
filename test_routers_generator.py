# test_routers_generator.py
"""تست تولید کامل پروژه‌ی FastAPI"""

import os
from src.services.schema_store import SchemaStore
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
    print("🔍 اتصال به SQLite...")
    store = SchemaStore()
    project = store.get_active_project()
    print(f"📦 پروژه: {project.name} ({project.fa_name})")

    tables = store.list_tables(project.id)
    print(f"📋 {len(tables)} جدول\n")

    project_root = os.path.join("generated", f"{project.name}_api")
    base_dir = os.path.join(project_root, "app")
    routers_dir = os.path.join(base_dir, "routers")
    auth_dir = os.path.join(base_dir, "auth")
    templates_dir = os.path.join("src", "services", "templates")

    os.makedirs(routers_dir, exist_ok=True)
    os.makedirs(auth_dir, exist_ok=True)

    print("📝 ساخت config.py...")
    _copy_template(
        os.path.join(templates_dir, "app_config.py"),
        os.path.join(base_dir, "config.py"),
    )

    print("\n🗄️  ساخت database.py...")
    _copy_template(
        os.path.join(templates_dir, "app_database.py"),
        os.path.join(base_dir, "database.py"),
    )

    print("\n🔐 ساخت auth/password.py...")
    _copy_template(
        os.path.join(templates_dir, "auth_password.py"),
        os.path.join(auth_dir, "password.py"),
    )

    print("\n🐍 تولید routers/*.py...")
    gen = RoutersGenerator(project, tables)
    files = gen.generate_all()
    for table_name, code in files.items():
        _write_file(os.path.join(routers_dir, f"{table_name}.py"), code)
        print(f"   ✅ {table_name}.py")

    print("\n🚀 ساخت main.py...")
    _copy_template(
        os.path.join(templates_dir, "app_main.py"),
        os.path.join(base_dir, "main.py"),
    )

    print("\n⚙️  ساخت .env.example...")
    _copy_template(
        os.path.join(templates_dir, "env_example.txt"),
        os.path.join(project_root, ".env.example"),
    )

    print("\n📦 ساخت requirements.txt...")
    _copy_template(
        os.path.join(templates_dir, "app_requirements.txt"),
        os.path.join(project_root, "requirements.txt"),
    )

    print("\n📖 ساخت README.md...")
    _copy_template(
        os.path.join(templates_dir, "app_readme.md"),
        os.path.join(project_root, "README.md"),
    )

    print("\n📦 ساخت __init__.py ها...")
    for pkg_dir in [base_dir, routers_dir, auth_dir]:
        init_path = os.path.join(pkg_dir, "__init__.py")
        if not os.path.exists(init_path):
            _write_file(init_path, "")
            print(f"   ✅ {init_path}")

    print(f"\n✅ پروژه کامل شد: {os.path.abspath(project_root)}")


if __name__ == "__main__":
    main()