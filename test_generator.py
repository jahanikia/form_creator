# test_generator.py
"""
اسکریپت تست تولید models.py
─────────────────────────────────
این اسکریپت رو از ریشه‌ی پروژه (form_creator/) اجرا کن:
    python test_generator.py

خروجی: یه پوشه‌ی generated/ می‌سازه و models_test.py رو داخلش می‌ذاره.
"""

import os
from src.services.schema_store import SchemaStore
from src.services.python_generator import PythonGenerator


def main():
    print("🔍 اتصال به SQLite...")
    store = SchemaStore()

    print("📦 بارگذاری پروژه‌ی فعال...")
    project = store.get_active_project()
    print(f"   → پروژه: {project.name} ({project.fa_name})")

    print("📋 بارگذاری جداول...")
    tables = store.list_tables(project.id)
    print(f"   → {len(tables)} جدول پیدا شد")

    if not tables:
        print("⚠️  هیچ جدولی توی این پروژه نیست!")
        return

    print("📁 بارگذاری گروه‌ها...")
    groups = store.list_groups(project.id)
    print(f"   → {len(groups)} گروه")

    print("\n🐍 تولید models.py...")
    gen = PythonGenerator(project, tables, groups)
    code = gen.generate_models()

    # ─── ذخیره در پوشه‌ی generated ───
    output_dir = os.path.join("generated", f"{project.name}_api", "app", "models")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "models.py")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)

    print(f"\n✅ فایل ساخته شد: {output_path}")
    print(f"   📊 {len(code):,} کاراکتر")
    print(f"   📋 {len(tables)} جدول")
    print(f"   📏 {code.count(chr(10)):,} خط")

    print("\n👁  می‌تونی فایل رو اینجا ببینی:")
    print(f"   {os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()