# src/services/mock_api.py
"""
شبیه‌ساز API — برای Prototype
─────────────────────────────────
به جای ارسال درخواست HTTP واقعی، فقط print می‌کنه
تا بتونیم ترتیب اجرای اکشن‌ها و payload رو ببینیم.
"""

import json
from datetime import datetime


class MockApiClient:
    """کلاینت Mock — همه چیز رو لاگ می‌کنه"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.log: list[str] = []

    # ═══════════════════════════════════════════════════════
    # فراخوانی یک endpoint
    # ═══════════════════════════════════════════════════════
    def call(self, method: str, endpoint: str, payload: dict | None = None) -> dict:
        """شبیه‌سازی یک درخواست HTTP"""
        full_url = self.base_url + endpoint
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        line = f"[{timestamp}] {method:6s} {full_url}"
        self.log.append(line)

        print("─" * 70)
        print(f"🚀 {line}")
        if payload:
            print(f"📦 Payload:")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print("📦 Payload: (بدون بدنه)")
        print(f"✅ Response: 200 OK")
        print("─" * 70)

        return {"ok": True, "status": 200, "echo": payload}

    # ═══════════════════════════════════════════════════════
    # اجرای زنجیره‌ای
    # ═══════════════════════════════════════════════════════
    def run_chain(self, actions: list, payload: dict) -> None:
        """اجرای همه‌ی دکمه‌ها به ترتیب order"""
        sorted_actions = sorted(actions, key=lambda a: a.order)

        print("\n")
        print("╔" + "═" * 68 + "╗")
        print("║" + " ▶ اجرای زنجیره‌ی اکشن‌ها ".center(68, " ") + "║")
        print("╚" + "═" * 68 + "╝")
        print(f"🔢 تعداد اکشن‌ها: {len(sorted_actions)}")
        print(f"📊 ترتیب: {' → '.join(a.label for a in sorted_actions)}")
        print()

        for i, action in enumerate(sorted_actions, 1):
            print(f"\n▶ [{i}/{len(sorted_actions)}] {action.label} ({action.action})")
            self.call(action.method, action.endpoint, payload)

        print("\n" + "═" * 70)
        print("✅ پایان اجرای زنجیره")
        print("═" * 70 + "\n")

    # ═══════════════════════════════════════════════════════
    # ابزارهای جانبی
    # ═══════════════════════════════════════════════════════
    def dump_log(self) -> str:
        """همه‌ی لاگ‌ها به صورت یک رشته"""
        return "\n".join(self.log)

    def clear_log(self) -> None:
        self.log.clear()