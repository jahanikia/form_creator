# src/models/custom_schema.py
"""
مدل‌های Schema Designer
─────────────────────────────────
• Project         → یک پروژه (مثلاً «فروشگاه»)
• CustomTable     → یک جدول (مثلاً users)
• CustomColumn    → یک فیلد (مثلاً first_name)
• CustomRelation  → رابطه‌ی بین دو جدول (FK)
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Optional


# ═══════════════════════════════════════════════════════════
# انواع داده‌ی پشتیبانی‌شده
# ═══════════════════════════════════════════════════════════
DATA_TYPES = [
    # عددی
    "INT", "INT UNSIGNED",
    "BIGINT", "BIGINT UNSIGNED",
    "SMALLINT", "SMALLINT UNSIGNED",
    "TINYINT", "TINYINT UNSIGNED",
    # اعشاری
    "DECIMAL(10,2)", "DECIMAL(15,2)",
    "FLOAT", "DOUBLE",
    # رشته
    "VARCHAR(50)", "VARCHAR(100)", "VARCHAR(150)",
    "VARCHAR(255)", "VARCHAR(500)",
    "TEXT", "LONGTEXT",
    # تاریخ/زمان
    "DATE", "TIME", "DATETIME", "TIMESTAMP",
    # بولی
    "BOOLEAN",
    # باینری
    "BLOB",
    # JSON
    "JSON",
    # ENUM
    "ENUM",
]

# پیشنهادهایی برای auto-fill بر اساس نوع
AUTO_FILL_HINTS = {
    "TIMESTAMP": ["now", "now_on_update"],
    "DATETIME":  ["now"],
    "DATE":      ["now"],
    "INT":       ["auto_increment"],
    "BIGINT":    ["auto_increment"],
}


# ═══════════════════════════════════════════════════════════
# Project — یک پروژه
# ═══════════════════════════════════════════════════════════
# src/models/custom_schema.py — فقط Project

@dataclass
class Project:
    id: Optional[int] = None
    name: str = "default"
    fa_name: str = ""
    description: str = ""
    db_type: str = "mysql"
    db_name: str = ""               # ⭐ جدید: نام دیتابیس MySQL
    is_default: bool = False        # ⭐ جدید
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

# ═══════════════════════════════════════════════════════════
# TableGroup — گروه‌بندی جداول
# ═══════════════════════════════════════════════════════════
@dataclass
class TableGroup:
    id: Optional[int] = None
    project_id: Optional[int] = None
    name: str = ""                    # auth
    fa_name: str = ""                 # احراز هویت
    color: str = "#0d6efd"            # رنگ نمایش
    icon: str = "📁"                  # آیکون
    order_index: int = 0
    is_default: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

# ═══════════════════════════════════════════════════════════
# CustomColumn — یک فیلد
# ═══════════════════════════════════════════════════════════
@dataclass
class CustomColumn:
    id: Optional[int] = None
    table_id: Optional[int] = None
    name: str = ""                    # first_name
    fa_name: str = ""                 # نام
    data_type: str = "VARCHAR(150)"   # نوع
    allow_null: bool = False
    default_value: str = ""           # "" یا "NULL" یا "CURRENT_TIMESTAMP"
    is_primary: bool = False
    is_unique: bool = False
    is_auto_increment: bool = False
    is_searchable: bool = True
    comment: str = ""
    order_index: int = 0

    # ─── کمکی ───
    def full_type(self) -> str:
        """نوع کامل با PRIMARY KEY / NULL / DEFAULT"""
        parts = [self.data_type]
        if self.allow_null:
            parts.append("NULL")
        else:
            parts.append("NOT NULL")
        if self.default_value:
            if self.default_value.upper() in ("CURRENT_TIMESTAMP", "NULL"):
                parts.append(f"DEFAULT {self.default_value}")
            else:
                parts.append(f"DEFAULT '{self.default_value}'")
        if self.is_auto_increment:
            parts.append("AUTO_INCREMENT")
        return " ".join(parts)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def create_primary_key() -> "CustomColumn":
        """فیلد id پیش‌فرض"""
        return CustomColumn(
            name="id",
            fa_name="شناسه",
            data_type="BIGINT",
            allow_null=False,
            is_primary=True,
            is_auto_increment=True,
            is_unique=True,
            order_index=0,
            comment="کلید اصلی",
        )


# ═══════════════════════════════════════════════════════════
# CustomTable — یک جدول
# ═══════════════════════════════════════════════════════════
@dataclass
class CustomTable:
    id: Optional[int] = None
    project_id: Optional[int] = None
    group_id: Optional[int] = None   # ⭐ جدید
    name: str = ""                    # users
    fa_name: str = ""                 # کاربران
    description: str = ""
    is_default: bool = False          # جدول پیش‌فرض؟
    order_index: int = 0
    columns: List[CustomColumn] = field(default_factory=list)

    # ─── کمکی ───
    def find_column(self, name: str) -> Optional[CustomColumn]:
        for c in self.columns:
            if c.name == name:
                return c
        return None

    def primary_key(self) -> Optional[CustomColumn]:
        for c in self.columns:
            if c.is_primary:
                return c
        return None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["columns"] = [c.to_dict() for c in self.columns]
        return d

    @staticmethod
    def create_empty(project_id: int, name: str = "new_table",
                     fa_name: str = "جدول جدید") -> "CustomTable":
        """جدول خالی با فیلد id"""
        t = CustomTable(
            project_id=project_id,
            name=name,
            fa_name=fa_name,
        )
        t.columns.append(CustomColumn.create_primary_key())
        return t


# ═══════════════════════════════════════════════════════════
# CustomRelation — رابطه‌ی FK
# ═══════════════════════════════════════════════════════════
@dataclass
class CustomRelation:
    id: Optional[int] = None
    from_table_id: Optional[int] = None
    from_column_id: Optional[int] = None
    to_table_id: Optional[int] = None
    to_column_id: Optional[int] = None
    relation_type: str = "many-to-one"   # many-to-one / one-to-many / one-to-one

    def to_dict(self) -> dict:
        return asdict(self)


# ═══════════════════════════════════════════════════════════
# اعتبارسنجی نام جدول/ستون
# ═══════════════════════════════════════════════════════════
import re

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
RESERVED_WORDS = {
    "select", "insert", "update", "delete", "from", "where",
    "table", "index", "primary", "key", "foreign", "references",
    "order", "group", "having", "join", "union",
}


def validate_name(name: str) -> tuple[bool, str]:
    """
    اعتبارسنجی نام جدول/ستون
    برمی‌گردونه: (is_valid, error_message)
    """
    if not name:
        return False, "نام نمی‌تونه خالی باشه"

    if not NAME_PATTERN.match(name):
        return False, "نام باید با حرف کوچک شروع بشه و فقط شامل a-z، 0-9 و _ باشه"

    if name in RESERVED_WORDS:
        return False, f"«{name}» یک کلمه‌ی رزرو شده در SQL است"

    if len(name) > 64:
        return False, "نام نمی‌تونه بیشتر از 64 کاراکتر باشه"

    return True, ""