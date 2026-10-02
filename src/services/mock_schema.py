# src/services/mock_schema.py
"""
ساختار mock دیتابیس برای تست Form Builder
─────────────────────────────────────────────
این ماژول سه جدول نمونه رو تعریف می‌کنه:
  • users        → کاربران
  • roles        → نقش‌ها
  • user_roles   → جدول واسط (many-to-many)

ساختار هر ستون:
  {
    "name": "email",           # نام ستون
    "type": "varchar(150)",    # نوع داده
    "nullable": False,         # اجازه NULL؟
    "key": "UNI",              # PRI / UNI / MUL / ""
    "default": None,           # مقدار پیش‌فرض
    "extra": ""                # auto_increment / on update ...
  }
"""

MOCK_SCHEMA: dict[str, list[dict]] = {
    # ═══════════════════════════════════════════════════════
    # جدول users
    # ═══════════════════════════════════════════════════════
    "users": [
        {
            "name": "id",
            "type": "bigint(20) unsigned",
            "nullable": False, "key": "PRI",
            "default": None, "extra": "auto_increment",
        },
        {
            "name": "email",
            "type": "varchar(150)",
            "nullable": False, "key": "UNI",
            "default": None, "extra": "",
        },
        {
            "name": "password",
            "type": "varchar(255)",
            "nullable": False, "key": "",
            "default": None, "extra": "",
        },
        {
            "name": "full_name",
            "type": "varchar(100)",
            "nullable": True, "key": "",
            "default": None, "extra": "",
        },
        {
            "name": "is_active",
            "type": "tinyint(1)",
            "nullable": False, "key": "",
            "default": "1", "extra": "",
        },
        {
            "name": "created_at",
            "type": "timestamp",
            "nullable": False, "key": "",
            "default": "CURRENT_TIMESTAMP", "extra": "",
        },
    ],

    # ═══════════════════════════════════════════════════════
    # جدول roles
    # ═══════════════════════════════════════════════════════
    "roles": [
        {
            "name": "id",
            "type": "bigint(20) unsigned",
            "nullable": False, "key": "PRI",
            "default": None, "extra": "auto_increment",
        },
        {
            "name": "name",
            "type": "varchar(50)",
            "nullable": False, "key": "UNI",
            "default": None, "extra": "",
        },
        {
            "name": "description",
            "type": "varchar(255)",
            "nullable": True, "key": "",
            "default": None, "extra": "",
        },
        {
            "name": "created_at",
            "type": "timestamp",
            "nullable": False, "key": "",
            "default": "CURRENT_TIMESTAMP", "extra": "",
        },
    ],

    # ═══════════════════════════════════════════════════════
    # جدول user_roles (many-to-many)
    # ═══════════════════════════════════════════════════════
    "user_roles": [
        {
            "name": "id",
            "type": "bigint(20) unsigned",
            "nullable": False, "key": "PRI",
            "default": None, "extra": "auto_increment",
        },
        {
            "name": "user_id",
            "type": "bigint(20) unsigned",
            "nullable": False, "key": "MUL",
            "default": None, "extra": "",
        },
        {
            "name": "role_id",
            "type": "bigint(20) unsigned",
            "nullable": False, "key": "MUL",
            "default": None, "extra": "",
        },
        {
            "name": "assigned_at",
            "type": "timestamp",
            "nullable": False, "key": "",
            "default": "CURRENT_TIMESTAMP", "extra": "",
        },
    ],
}


# ═══════════════════════════════════════════════════════════
# توابع کمکی
# ═══════════════════════════════════════════════════════════
def list_tables() -> list[str]:
    """لیست نام جداول"""
    return list(MOCK_SCHEMA.keys())


def get_columns(table_name: str) -> list[dict]:
    """ستون‌های یک جدول"""
    return MOCK_SCHEMA.get(table_name, [])


def get_primary_key(table_name: str) -> str | None:
    """نام ستون کلید اصلی یک جدول"""
    for col in get_columns(table_name):
        if col.get("key") == "PRI":
            return col["name"]
    return None

def get_column(table_name: str, col_name: str) -> dict | None:
    """اطلاعات یک ستون خاص"""
    for c in get_columns(table_name):
        if c["name"] == col_name:
            return c
    return None