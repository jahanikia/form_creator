# src/services/python_generator.py
"""
PythonGenerator — تولید کد FastAPI از روی Schema
─────────────────────────────────
قدم ۵.۱: تولید models.py (SQLAlchemy 2.0)
"""

from typing import List, Optional
from src.models.custom_schema import (
    Project, CustomTable, CustomColumn, TableGroup,
)


# ═══════════════════════════════════════════════════════════
# فیلدهای حساس (hardcode)
# ═══════════════════════════════════════════════════════════
SENSITIVE_FIELDS = {
    "users":           {"password"},
    "sessions":        {"token"},
    "password_resets": {"token"},
    "jwt_blacklist":   {"token"},
}

# ═══════════════════════════════════════════════════════════
# جدول‌هایی که جدول واسط many-to-many هستن
# ═══════════════════════════════════════════════════════════
PURE_JUNCTION_TABLES = {
    "user_roles",        # user_id + role_id
    "role_permissions",  # role_id + permission_id
}


class PythonGenerator:
    """تولیدکننده‌ی کد FastAPI"""

    def __init__(self, project: Project,
                 tables: List[CustomTable],
                 groups: Optional[List[TableGroup]] = None):
        self.project = project
        self.tables = tables
        self.groups = groups or []
        self._table_by_name = {t.name: t for t in tables}

    # ═══════════════════════════════════════════════════════
    # ابزار کمکی: نام کلاس پایتون از نام جدول
    # ═══════════════════════════════════════════════════════
    @staticmethod
    def _class_name(table_name: str) -> str:
        """
        user_profiles → UserProfile
        users         → User
        roles         → Role
        permissions   → Permission
        sessions      → Session
        otp_codes     → OtpCode
        """
        # ─── اسم‌های خاص ───
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

        # ─── fallback: snake_case → PascalCase ───
        return "".join(part.capitalize() for part in table_name.split("_"))

    # ═══════════════════════════════════════════════════════
    # ابزار کمکی: تبدیل نوع MySQL → نوع SQLAlchemy
    # ═══════════════════════════════════════════════════════
    def _sqlalchemy_type(self, col: CustomColumn) -> tuple[str, str]:
        """
        برمی‌گردونه: (نوع_python، نوع_sqlalchemy)
        مثلاً: ("int", "BigInteger")  یا  ("str", "String(150)")
        """
        dtype = col.data_type.upper().strip()

        # ─── عددی ───
        if dtype in ("TINYINT", "TINYINT UNSIGNED"):
            return "int", "SmallInteger"
        if dtype in ("SMALLINT", "SMALLINT UNSIGNED"):
            return "int", "SmallInteger"
        if dtype in ("INT", "INT UNSIGNED"):
            return "int", "Integer"
        if dtype in ("BIGINT", "BIGINT UNSIGNED"):
            return "int", "BigInteger"

        # ─── اعشاری ───
        if dtype.startswith("DECIMAL"):
            return "Decimal", f"Numeric({dtype[8:-1]})"  # DECIMAL(10,2) → Numeric(10,2)
        if dtype == "FLOAT":
            return "float", "Float"
        if dtype == "DOUBLE":
            return "float", "Float"

        # ─── رشته ───
        if dtype.startswith("VARCHAR"):
            size = dtype[8:-1]  # VARCHAR(150) → 150
            return "str", f"String({size})"
        if dtype in ("TEXT", "LONGTEXT"):
            return "str", "Text"

        # ─── تاریخ/زمان ───
        if dtype == "DATE":
            return "date", "Date"
        if dtype == "TIME":
            return "time", "Time"
        if dtype in ("DATETIME", "TIMESTAMP"):
            return "datetime", "DateTime"

        # ─── بولی ───
        if dtype == "BOOLEAN":
            return "bool", "Boolean"

        # ─── باینری ───
        if dtype == "BLOB":
            return "bytes", "LargeBinary"

        # ─── JSON ───
        if dtype == "JSON":
            return "dict", "JSON"

        # ─── ENUM (فعلاً String) ───
        if dtype == "ENUM":
            return "str", "String(50)"

        # ─── fallback ───
        return "str", "String(255)"

    # ═══════════════════════════════════════════════════════
    # ابزار کمکی: تشخیص FK از comment
    # ═══════════════════════════════════════════════════════
    def _fk_target(self, col: CustomColumn) -> Optional[str]:
        """اگه ستون FK باشه، نام جدول مقصد رو برمی‌گردونه"""
        if col.comment and col.comment.startswith("FK → "):
            return col.comment.replace("FK → ", "").strip()
        return None

    # ═══════════════════════════════════════════════════════
    # ابزار کمکی: تشخیص روابط (relationship)
    # ═══════════════════════════════════════════════════════
    def _build_relationships(self) -> dict:
        """
        برای هر جدول، لیست relationshipهای outgoing و incoming رو می‌سازه.
        برمی‌گردونه: {
          "users": {
            "outgoing": [],  # FKهایی که این جدول داره (many-to-one)
            "incoming": [    # FKهایی که به این جدول اشاره می‌کنن (one-to-many)
              {"from_table": "user_profiles", "from_col": "user_id",
               "back_populates": "profile", "kind": "one-to-one"},
              ...
            ]
          }
        }
        """
        rels = {t.name: {"outgoing": [], "incoming": []} for t in self.tables}

        for table in self.tables:
            for col in table.columns:
                target = self._fk_target(col)
                if not target or target not in self._table_by_name:
                    continue

                # outgoing از دید جدول فعلی
                rels[table.name]["outgoing"].append({
                    "column": col.name,
                    "target_table": target,
                    "nullable": col.allow_null,
                })

                # incoming از دید جدول مقصد
                # تشخیص one-to-one: اگه col.is_unique
                kind = "one-to-one" if col.is_unique else "one-to-many"

                rels[target]["incoming"].append({
                    "from_table": table.name,
                    "from_col": col.name,
                    "nullable": col.allow_null,
                    "kind": kind,
                })

        return rels

    # ═══════════════════════════════════════════════════════
    # ابزار کمکی: تولید back_populates
    # ═══════════════════════════════════════════════════════
    @staticmethod
    def _back_populates_name(table_name: str, fk_col: str) -> str:
        """user_profiles.user_id → 'user_profiles' برای back_populates"""
        return table_name

    @staticmethod
    def _forward_relationship_name(fk_col: str, target_table: str) -> str:
        """user_id → 'user'  (حذف _id و singular)"""
        name = fk_col.replace("_id", "")
        return name

    # ═══════════════════════════════════════════════════════
    # تولید یک ستون
    # ═══════════════════════════════════════════════════════

    def _render_column(self, col: CustomColumn, table_name: str) -> str:
        py_type, sa_type = self._sqlalchemy_type(col)
        fk_target = self._fk_target(col)

        # ─── نوع Mapped ───
        if col.allow_null:
            mapped_type = f"{py_type} | None"
        else:
            mapped_type = py_type

        # ─── آرگومان‌های mapped_column ───
        args = []

        # ⭐ ترتیب مهمه: نوع اول، بعد ForeignKey
        if fk_target and fk_target in self._table_by_name:
            # اول نوع
            args.append("BigInteger")
            # بعد FK
            args.append(f'ForeignKey("{fk_target}.id")')
        else:
            args.append(sa_type)

        # nullable
        if not col.allow_null:
            args.append("nullable=False")

        # primary_key
        if col.is_primary:
            args.append("primary_key=True")
            args.append("autoincrement=True")

        # unique
        if col.is_unique and not col.is_primary:
            args.append("unique=True")

        # default
        if col.default_value and col.default_value.strip():
            dv = col.default_value.strip().upper()
            if dv == "CURRENT_TIMESTAMP":
                args.append("server_default=func.now()")
            elif dv == "NULL":
                pass
            elif dv.isdigit() or (dv.startswith("-") and dv[1:].isdigit()):
                args.append(f"default={dv}")
            else:
                args.append(f'default="{col.default_value}"')

        # comment
        if col.fa_name:
            comment = col.fa_name
            if col.comment and not col.comment.startswith("FK → ") and not col.comment.startswith("enum:"):
                comment = f"{col.fa_name} — {col.comment}"
            comment = comment.replace('"', '\\"')
            args.append(f'comment="{comment}"')

        # ─── اسمبل ───
        args_str = ",\n        ".join(args)
        line = f'    {col.name}: Mapped[{mapped_type}] = mapped_column(\n        {args_str}\n    )'
        return line

    # ═══════════════════════════════════════════════════════
    # تولید relationship برای outgoing (many-to-one)
    # ═══════════════════════════════════════════════════════
    def _render_outgoing_rel(self, rel: dict, from_table: str) -> str:
        target = rel["target_table"]
        target_cls = self._class_name(target)
        rel_name = self._forward_relationship_name(rel["column"], target)

        if rel["nullable"]:
            mapped = f'Mapped["{target_cls}"]'
            # relationship با Optional
            return (
                f'    {rel_name}: Mapped["{target_cls} | None"] = relationship(\n'
                f'        "{target_cls}",\n'
                f'        back_populates="{from_table}",\n'
                f'        foreign_keys="[{self._class_name(from_table)}.{rel["column"]}]",\n'
                f'    )'
            )
        return (
            f'    {rel_name}: Mapped["{target_cls}"] = relationship(\n'
            f'        "{target_cls}",\n'
            f'        back_populates="{from_table}",\n'
            f'        foreign_keys="[{self._class_name(from_table)}.{rel["column"]}]",\n'
            f'    )'
        )

    # ═══════════════════════════════════════════════════════
    # تولید relationship برای incoming (one-to-many / one-to-one)
    # ═══════════════════════════════════════════════════════
    def _render_incoming_rel(self, rel: dict) -> str:
        from_t = rel["from_table"]
        from_cls = self._class_name(from_t)
        rel_name = from_t  # users → user_profiles
        kind = rel["kind"]

        if kind == "one-to-one":
            return (
                f'    {rel_name}: Mapped["{from_cls} | None"] = relationship(\n'
                f'        "{from_cls}",\n'
                f'        back_populates="{rel["from_col"].replace("_id", "")}",\n'
                f'        uselist=False,\n'
                f'    )'
            )
        # one-to-many
        return (
            f'    {rel_name}: Mapped[list["{from_cls}"]] = relationship(\n'
            f'        "{from_cls}",\n'
            f'        back_populates="{rel["from_col"].replace("_id", "")}",\n'
            f'    )'
        )

    # ═══════════════════════════════════════════════════════
    # تولید یک جدول (کلاس SQLAlchemy)
    # ═══════════════════════════════════════════════════════
    def _render_table(self, table: CustomTable, rels: dict) -> str:
        cls_name = self._class_name(table.name)

        # ─── docstring ───
        fa_name = table.fa_name or table.name
        lines = [
            f'class {cls_name}(Base):',
            f'    """{fa_name}"""',
            f'    __tablename__ = "{table.name}"',
            '',
        ]

        # ─── ستون‌ها ───
        for col in table.columns:
            lines.append(self._render_column(col, table.name))
            lines.append('')

        # ─── relationshipهای outgoing (many-to-one) ───
        for rel in rels[table.name]["outgoing"]:
            lines.append(self._render_outgoing_rel(rel, table.name))
            lines.append('')

        # ─── relationshipهای incoming (one-to-many / one-to-one) ───
        for rel in rels[table.name]["incoming"]:
            lines.append(self._render_incoming_rel(rel))
            lines.append('')

        # حذف آخرین خط خالی اضافی
        while lines and lines[-1] == '':
            lines.pop()

        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════
    # تولید کل models.py
    # ═══════════════════════════════════════════════════════
    def generate_models(self) -> str:
        rels = self._build_relationships()

        header = '''# app/models/models.py
"""
Auto-generated by Py App Maker
Project: {project_name}
DO NOT EDIT MANUALLY
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, Date, DateTime, Float, ForeignKey,
    Integer, JSON, LargeBinary, Numeric, SmallInteger,
    String, Text, Time, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base کلاس برای همه‌ی مدل‌ها"""
    pass


# ═══════════════════════════════════════════════════════════
# جداول
# ═══════════════════════════════════════════════════════════
'''.format(project_name=self.project.name)

        # ─── ترتیب جداول: اول والدها (بدون FK)، بعد بقیه ───
        sorted_tables = self._sort_tables_by_dependency()

        parts = [header]
        for table in sorted_tables:
            parts.append('')
            parts.append(f'# ─── {table.fa_name or table.name} ───')
            parts.append(self._render_table(table, rels))
            parts.append('')
            parts.append('')

        # ─── __all__ ───
        class_names = [self._class_name(t.name) for t in sorted_tables]
        parts.append('# ═══════════════════════════════════════════════════════════')
        parts.append('# __all__')
        parts.append('# ═══════════════════════════════════════════════════════════')
        parts.append('__all__ = [')
        parts.append('    "Base",')
        for cn in class_names:
            parts.append(f'    "{cn}",')
        parts.append(']')
        parts.append('')

        return "\n".join(parts)

    # ═══════════════════════════════════════════════════════
    # مرتب‌سازی جداول بر اساس وابستگی (توپولوژیک)
    # ═══════════════════════════════════════════════════════
    def _sort_tables_by_dependency(self) -> List[CustomTable]:
        """جداولی که FK دارن بعد از جداول والد بیان"""
        table_map = {t.name: t for t in self.tables}
        visited = set()
        result = []

        def visit(t: CustomTable):
            if t.name in visited:
                return
            visited.add(t.name)
            # اول والدها
            for col in t.columns:
                target = self._fk_target(col)
                if target and target in table_map and target != t.name:
                    visit(table_map[target])
            result.append(t)

        for t in self.tables:
            visit(t)

        return result