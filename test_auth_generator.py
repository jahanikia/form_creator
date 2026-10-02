# test_auth_generator.py
"""تست تولید auth/* و routers/auth.py"""

import os
from src.services.schema_store import SchemaStore


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


def main():
    store = SchemaStore()
    project = store.get_active_project()

    project_root = os.path.join("generated", f"{project.name}_api")
    base_dir = os.path.join(project_root, "app")
    auth_dir = os.path.join(base_dir, "auth")
    routers_dir = os.path.join(base_dir, "routers")
    templates_dir = os.path.join("src", "services", "templates")

    os.makedirs(auth_dir, exist_ok=True)
    os.makedirs(routers_dir, exist_ok=True)

    print("🔐 تولید auth/jwt_handler.py...")
    _copy_template(
        os.path.join(templates_dir, "auth_jwt_handler.py"),
        os.path.join(auth_dir, "jwt_handler.py"),
    )

    print("\n🔐 تولید auth/dependencies.py...")
    _copy_template(
        os.path.join(templates_dir, "auth_dependencies.py"),
        os.path.join(auth_dir, "dependencies.py"),
    )

    print("\n🔐 تولید routers/auth.py...")
    _copy_template(
        os.path.join(templates_dir, "auth_router.py"),
        os.path.join(routers_dir, "auth.py"),
    )

    print("\n✅ auth کامل شد!")


if __name__ == "__main__":
    main()