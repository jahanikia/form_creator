# src/services/schemas_generator.py
"""
SchemasGenerator — تولید schemas.py (Pydantic v2) از روی Schema
─────────────────────────────────
قدم ۵.۲: تولید schemas.py

برای هر جدول ۴ کلاس می‌سازه:
  • {Model}Base      → فیلدهای مشترک
  • {Model}Create    → POST (ورودی) — شامل password/token
  • {Model}Update    → PATCH — همه optional
  • {Model}Response  → خروجی (بدون فیلدهای حساس)
"""

from typing import List, Optional, Set
from src.models.custom_schema import Project, CustomTable, CustomColumn


# ═══════════════════════════════════════════════════════════
# فیلدهای حساس (نباید توی Response بیان)
# ═══════════════════════════════════════════════════════════
SENSITIVE_FIELDS = {
    "users":           {"password"},
    "sessions":        {"token"},
    "password_resets": {"token"},
    "jwt_blacklist":   {"token"},
}


class SchemasGenerator:
    """تولیدکننده‌ی schemas.py (Pydantic v2)"""

    def __init__(self, project: Project, tables: List[CustomTable]):
        self.project = project
        self.tables = tables
        self._table_by_name = {t.name: t for t in tables}

    # ═══════════════════════════════════════════════════════
    # نام کلاس (هم‌راستا با python_generator)
    # ═══════════════════════════════════════════════════════
    @staticmethod
    def _class_name(table_name: str) -> str:
        SPECIAL = {
            "users":           "User",
            "roles":           "Role",
            "permissions":     "Permission",
            "sessions":        "Session",
            "user_profiles":   "UserProfile",
            "user_roles":      "UserRole",
            "role_permissions":"RolePermission",
            "password_resets": "PasswordReset",
            "otp_codes":       "OtpCode",
            "login_attempts":  "LoginAttempt",
            "user_activities": "UserActivity",
            "jwt_blacklist":   "JwtBlacklist",
        }
        if table_name in SPECIAL:
            return SPECIAL[table_name]
        return "".join(part.capitalize() for part in table_name.split("_"))

    # ═══════════════════════════════════════════════════════
    # ابزار: تشخیص نوع پایتون
    # ═══════════════════════════════════════════════════════
    @staticmethod
    def _py_type(col: CustomColumn) -> str:
        dtype = col.data_type.upper().strip()

        if dtype in ("TINYINT", "TINYINT UNSIGNED",
                     "SMALLINT", "SMALLINT UNSIGNED",
                     "INT", "INT UNSIGNED",
                     "BIGINT", "BIGINT UNSIGNED"):
            return "int"
        if dtype.startswith("DECIMAL"):
            return "Decimal"
        if dtype in ("FLOAT", "DOUBLE"):
            return "float"
        if dtype.startswith("VARCHAR") or dtype in ("TEXT", "LONGTEXT"):
            return "str"
        if dtype == "DATE":
            return "date"
        if dtype == "TIME":
            return "time"
        if dtype in ("DATETIME", "TIMESTAMP"):
            return "datetime"
        if dtype == "BOOLEAN":
            return "bool"
        if dtype == "BLOB":
            return "bytes"
        if dtype == "JSON":
            return "dict"
        if dtype == "ENUM":
            return "str"
        return "str"

    # ═══════════════════════════════════════════════════════
    # ابزار: تشخیص FK از comment
    # ═══════════════════════════════════════════════════════
    @staticmethod
    def _fk_target(col: CustomColumn) -> Optional[str]:
        if col.comment and col.comment.startswith("FK → "):
            return col.comment.replace("FK → ", "").strip()
        return None

    # ═══════════════════════════════════════════════════════
    # ابزار: تولید خط یک فیلد Pydantic
    # ═══════════════════════════════════════════════════════
    def _render_field(
        self,
        col: CustomColumn,
        *,
        optional: bool,
        with_default: bool,
        is_create: bool = False,
        is_update: bool = False,
    ) -> str:
        """
        ساخت یک خط فیلد Pydantic.
        مثال: `    first_name: str = Field(..., max_length=100)`
        """
        py_type = self._py_type(col)

        # ─── EmailStr ───
        if col.name == "email" or col.name.endswith("_email"):
            py_type = "EmailStr"

        # ─── نوع نهایی ───
        # توی Update: همه Optional
        if optional:
            final_type = f"Optional[{py_type}]"
        else:
            final_type = py_type

        # ─── آرگومان‌های Field ───
        field_args = []

        # required یا default
        if is_update:
            # توی Update همه پیش‌فرض None
            field_args.append("None")
        elif col.allow_null:
            field_args.append("None")
        elif with_default and col.default_value and col.default_value.strip():
            dv = col.default_value.strip().upper()
            if dv == "CURRENT_TIMESTAMP":
                # به SQLAlchemy/Pydantic واگذار می‌کنیم → None
                field_args.append("None")
            elif dv == "NULL":
                field_args.append("None")
            elif dv in ("1", "0"):
                # BOOLEAN
                field_args.append("True" if dv == "1" else "False")
            elif dv.replace(".", "").replace("-", "").isdigit():
                field_args.append(dv)
            else:
                field_args.append(f'"{col.default_value}"')
        else:
            # required
            field_args.append("...")

        # ─── محدودیت‌ها ───
        constraints = []

        dtype = col.data_type.upper().strip()

        # max_length برای VARCHAR
        if dtype.startswith("VARCHAR"):
            size = dtype[8:-1]
            constraints.append(f"max_length={size}")

        # min_length برای password
        if col.name == "password" and is_create:
            constraints.append("min_length=6")

        # برای DECIMAL — max_digits و decimal_places
        if dtype.startswith("DECIMAL"):
            inner = dtype[8:-1]
            if "," in inner:
                digits, places = [s.strip() for s in inner.split(",")]
                constraints.append(f"max_digits={digits}")
                constraints.append(f"decimal_places={places}")

        # ─── اسمبل Field(...) ───
        all_args = field_args + constraints
        args_str = ", ".join(all_args)

        return f"    {col.name}: {final_type} = Field({args_str})"

    # ═══════════════════════════════════════════════════════
    # فیلتر کردن ستون‌ها برای هر کلاس
    # ═══════════════════════════════════════════════════════
    @staticmethod
    def _is_pk(col: CustomColumn) -> bool:
        return col.is_primary

    @staticmethod
    def _is_timestamp_audit(col: CustomColumn) -> bool:
        return col.name in ("created_at", "updated_at")

    def _base_columns(self, table: CustomTable) -> List[CustomColumn]:
        """ستون‌های Base: بدون PK، بدون audit timestamps، بدون حساس‌ها، بدون FK"""
        sensitive = SENSITIVE_FIELDS.get(table.name, set())
        result = []
        for col in table.columns:
            if self._is_pk(col):
                continue
            if self._is_timestamp_audit(col):
                continue
            if col.name in sensitive:
                continue
            if self._fk_target(col):
                continue  # FK → فقط توی Create میاد
            result.append(col)
        return result

    def _create_only_columns(self, table: CustomTable) -> List[CustomColumn]:
        """ستون‌های اضافی که فقط توی Create میان: FK + حساس‌ها"""
        sensitive = SENSITIVE_FIELDS.get(table.name, set())
        result = []
        for col in table.columns:
            if self._is_pk(col):
                continue
            if self._is_timestamp_audit(col):
                continue
            # FK یا حساس
            if self._fk_target(col) or col.name in sensitive:
                result.append(col)
        return result

    def _response_only_columns(self, table: CustomTable) -> List[CustomColumn]:
        """ستون‌های اضافی که فقط توی Response میان: PK + audit timestamps + FK"""
        sensitive = SENSITIVE_FIELDS.get(table.name, set())
        result = []
        for col in table.columns:
            if col.name in sensitive:
                continue
            if self._is_pk(col):
                result.append(col)
            elif self._is_timestamp_audit(col):
                result.append(col)
            elif self._fk_target(col):
                result.append(col)
        return result

    def _update_columns(self, table: CustomTable) -> List[CustomColumn]:
        """ستون‌های Update: همه‌ی فیلدهای غیر-PK، غیر-audit + حساس‌های قابل تغییر"""
        sensitive = SENSITIVE_FIELDS.get(table.name, set())
        result = []
        for col in table.columns:
            if self._is_pk(col):
                continue
            if self._is_timestamp_audit(col):
                continue
            # FK → توی Update معمولاً تغییر نمی‌کنه، ولی برای انعطاف می‌ذاریم
            # حساس‌ها → توی Update میان (مثل تغییر password)
            result.append(col)
        return result

    # ═══════════════════════════════════════════════════════
    # تولید یک جدول (۴ کلاس)
    # ═══════════════════════════════════════════════════════
    def _render_table(self, table: CustomTable) -> str:
        cls = self._class_name(table.name)
        fa = table.fa_name or table.name

        lines = []
        lines.append(f"# ═══════════════════════════════════════════════════════════")
        lines.append(f"# {fa}")
        lines.append(f"# ═══════════════════════════════════════════════════════════")

        # ─── Base ───
        base_cols = self._base_columns(table)
        lines.append(f"class {cls}Base(BaseModel):")
        lines.append(f'    """{fa} — فیلدهای مشترک"""')
        if base_cols:
            for col in base_cols:
                lines.append(self._render_field(col, optional=col.allow_null,
                                                 with_default=True))
        else:
            lines.append("    pass")
        lines.append("")
        lines.append("")

        # ─── Create ───
        create_extra = self._create_only_columns(table)
        lines.append(f"class {cls}Create({cls}Base):")
        lines.append(f'    """{fa} — برای POST"""')
        if create_extra:
            for col in create_extra:
                # توی Create، حساس‌ها required (مثلاً password)
                is_sensitive = col.name in SENSITIVE_FIELDS.get(table.name, set())
                if is_sensitive:
                    lines.append(self._render_field(
                        col, optional=False, with_default=False,
                        is_create=True,
                    ))
                else:
                    # FK → اگه allow_null باشه، اختیاری
                    lines.append(self._render_field(
                        col, optional=col.allow_null, with_default=True,
                        is_create=True,
                    ))
        else:
            lines.append("    pass")
        lines.append("")
        lines.append("")

        # ─── Update ───
        update_cols = self._update_columns(table)
        lines.append(f"class {cls}Update(BaseModel):")
        lines.append(f'    """{fa} — برای PATCH (همه اختیاری)"""')
        if update_cols:
            for col in update_cols:
                lines.append(self._render_field(
                    col, optional=True, with_default=False, is_update=True,
                ))
        else:
            lines.append("    pass")
        lines.append("")
        lines.append("")

        # ─── Response ───
        response_extra = self._response_only_columns(table)
        lines.append(f"class {cls}Response({cls}Base):")
        lines.append(f'    """{fa} — خروجی (بدون فیلدهای حساس)"""')
        if response_extra:
            for col in response_extra:
                lines.append(self._render_field(
                    col, optional=col.allow_null, with_default=True,
                ))
        else:
            lines.append("    pass")
        lines.append("")
        lines.append("    model_config = ConfigDict(from_attributes=True)")
        lines.append("")
        lines.append("")

        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════
    # تولید کل schemas.py
    # ═══════════════════════════════════════════════════════
    def generate_schemas(self) -> str:
        header = f'''# app/schemas/schemas.py
"""
Auto-generated by Py App Maker
Project: {self.project.name}
DO NOT EDIT MANUALLY
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ═══════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════
'''

        parts = [header]
        for table in self.tables:
            parts.append("")
            parts.append(self._render_table(table))

        # ─── __all__ ───
        class_names = [self._class_name(t.name) for t in self.tables]
        all_names = []
        for cn in class_names:
            all_names.extend([
                f"{cn}Base",
                f"{cn}Create",
                f"{cn}Update",
                f"{cn}Response",
            ])

        parts.append("")
        parts.append("# ═══════════════════════════════════════════════════════════")
        parts.append("# __all__")
        parts.append("# ═══════════════════════════════════════════════════════════")
        parts.append("__all__ = [")
        for name in all_names:
            parts.append(f'    "{name}",')
        parts.append("]")
        parts.append("")

        return "\n".join(parts) 