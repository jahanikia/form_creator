# clean_pycache.py
"""
پاک‌کننده‌ی __pycache__
─────────────────────────────────
همه‌ی پوشه‌های __pycache__ و فایل‌های .pyc رو حذف می‌کنه.

اجرا:
    python clean_pycache.py
    python clean_pycache.py --dry-run     # فقط نشون بده، پاک نکن
"""

import os
import shutil
import sys
import argparse

# ⭐ جلوگیری از تولید __pycache__ جدید
sys.dont_write_bytecode = True


# ═══════════════════════════════════════════════════════════
SKIP_DIRS = {".venv", "venv", "env", ".git", "node_modules", ".idea", ".vscode"}


def clean_pycache(root: str = ".", dry_run: bool = False) -> int:
    """پاک کردن __pycache__ ها و .pyc ها"""
    count = 0

    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # پوشه‌های ناخواسته رو نادیده بگیر
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        # ─── __pycache__ ───
        if "__pycache__" in dirnames:
            full = os.path.join(dirpath, "__pycache__")
            if dry_run:
                print(f"🔍 [DRY] حذف می‌شود: {full}")
            else:
                try:
                    shutil.rmtree(full)
                    print(f"🗑  حذف شد: {full}")
                except Exception as e:
                    print(f"⚠️  خطا در {full}: {e}")
                    continue
            count += 1
            dirnames.remove("__pycache__")

        # ─── .pyc / .pyo تکی ───
        for f in filenames:
            if f.endswith((".pyc", ".pyo")):
                full = os.path.join(dirpath, f)
                if dry_run:
                    print(f"🔍 [DRY] حذف می‌شود: {full}")
                else:
                    try:
                        os.remove(full)
                        print(f"🗑  حذف شد: {full}")
                    except Exception as e:
                        print(f"⚠️  خطا در {full}: {e}")
                        continue
                count += 1

    return count


# ═══════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="پاک کردن __pycache__ ها")
    parser.add_argument("--dry-run", action="store_true",
                        help="فقط نشون بده، پاک نکن")
    parser.add_argument("--path", default=".",
                        help="مسیر ریشه (پیش‌فرض: پروژه فعلی)")
    args = parser.parse_args()

    print("═" * 60)
    print("🧹 پاک‌کننده‌ی __pycache__")
    print("═" * 60)
    print(f"📍 مسیر: {os.path.abspath(args.path)}")
    if args.dry_run:
        print("🔍 حالت DRY-RUN (فقط نمایش)")
    print("─" * 60 + "\n")

    count = clean_pycache(args.path, dry_run=args.dry_run)

    print("\n" + "─" * 60)
    if count == 0:
        print("✨ هیچ __pycache__ یا .pyc پیدا نشد.")
    else:
        print(f"✅ {count} مورد پاک شد.")
    print("═" * 60)


if __name__ == "__main__":
    main()