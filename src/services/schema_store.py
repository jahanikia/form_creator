# src/services/schema_store.py
"""
SchemaStore — ذخیره‌سازی Schema در SQLite
─────────────────────────────────
• چند پروژه
• گروه‌بندی جداول
• تنظیمات سراسری (app_settings) و پروژه (project_settings)
"""

import os
import sqlite3
import dataclasses
from typing import List, Optional

from src.models.custom_schema import (
    Project, CustomTable, CustomColumn, CustomRelation, TableGroup,
)


DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "schemas.db")


# ═══════════════════════════════════════════════════════════
def row_to_model(row, model_cls):
    """تبدیل Row به dataclass با فیلتر کلیدها"""
    valid_fields = {f.name for f in dataclasses.fields(model_cls)}
    data = {k: v for k, v in dict(row).items() if k in valid_fields}
    return model_cls(**data)


# ═══════════════════════════════════════════════════════════
SCHEMA_SQL = """
-- ═══ تنظیمات سراسری برنامه ═══
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT DEFAULT ''
);

-- ═══ پروژه‌ها ═══
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    fa_name TEXT DEFAULT '',
    description TEXT DEFAULT '',
    db_type TEXT DEFAULT 'mysql',
    db_name TEXT DEFAULT '',
    is_default INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ═══ گروه‌ها ═══
CREATE TABLE IF NOT EXISTS table_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    fa_name TEXT DEFAULT '',
    color TEXT DEFAULT '#0d6efd',
    icon TEXT DEFAULT '📁',
    order_index INTEGER DEFAULT 0,
    is_default INTEGER DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE(project_id, name)
);

-- ═══ جداول ═══
CREATE TABLE IF NOT EXISTS custom_tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    group_id INTEGER,
    name TEXT NOT NULL,
    fa_name TEXT DEFAULT '',
    description TEXT DEFAULT '',
    is_default INTEGER DEFAULT 0,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES table_groups(id) ON DELETE SET NULL,
    UNIQUE(project_id, name)
);

-- ═══ فیلدها ═══
CREATE TABLE IF NOT EXISTS custom_columns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    fa_name TEXT DEFAULT '',
    data_type TEXT NOT NULL,
    allow_null INTEGER DEFAULT 0,
    default_value TEXT DEFAULT '',
    is_primary INTEGER DEFAULT 0,
    is_unique INTEGER DEFAULT 0,
    is_auto_increment INTEGER DEFAULT 0,
    is_searchable INTEGER DEFAULT 1,
    comment TEXT DEFAULT '',
    order_index INTEGER DEFAULT 0,
    FOREIGN KEY (table_id) REFERENCES custom_tables(id) ON DELETE CASCADE,
    UNIQUE(table_id, name)
);

-- ═══ روابط ═══
CREATE TABLE IF NOT EXISTS custom_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_table_id INTEGER NOT NULL,
    from_column_id INTEGER NOT NULL,
    to_table_id INTEGER NOT NULL,
    to_column_id INTEGER NOT NULL,
    relation_type TEXT DEFAULT 'many-to-one',
    FOREIGN KEY (from_table_id) REFERENCES custom_tables(id) ON DELETE CASCADE,
    FOREIGN KEY (to_table_id) REFERENCES custom_tables(id) ON DELETE CASCADE
);

-- ═══ تنظیمات پروژه ═══
CREATE TABLE IF NOT EXISTS project_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT DEFAULT '',
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE(project_id, key)
);

-- ═══ ایندکس‌ها ═══
CREATE INDEX IF NOT EXISTS idx_tables_project ON custom_tables(project_id);
CREATE INDEX IF NOT EXISTS idx_tables_group ON custom_tables(group_id);
CREATE INDEX IF NOT EXISTS idx_columns_table ON custom_columns(table_id);
CREATE INDEX IF NOT EXISTS idx_groups_project ON table_groups(project_id);
"""


# ═══════════════════════════════════════════════════════════
class SchemaStore:
    """ذخیره‌ساز Schema در SQLite"""

    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)
            self._migrate(conn)

    def _migrate(self, conn):
        """مهاجرت‌های سبک"""
        # custom_tables.group_id
        cols = [r[1] for r in conn.execute("PRAGMA table_info(custom_tables)")]
        if "group_id" not in cols:
            try:
                conn.execute("ALTER TABLE custom_tables ADD COLUMN group_id INTEGER")
                conn.commit()
                print("✅ مهاجرت: ستون group_id اضافه شد")
            except Exception as e:
                print(f"⚠️ {e}")

        # projects.fa_name
        pcols = [r[1] for r in conn.execute("PRAGMA table_info(projects)")]
        for col, typ, default in [
            ("fa_name", "TEXT", "''"),
            ("db_name", "TEXT", "''"),
            ("is_default", "INTEGER", "0"),
        ]:
            if col not in pcols:
                try:
                    conn.execute(
                        f"ALTER TABLE projects ADD COLUMN {col} {typ} DEFAULT {default}"
                    )
                    conn.commit()
                    print(f"✅ مهاجرت: projects.{col} اضافه شد")
                except Exception as e:
                    print(f"⚠️ {e}")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # ═════════════════════════════════════════════
    # App Settings (سراسری)
    # ═════════════════════════════════════════════
    def get_app_setting(self, key: str, default: str = "") -> str:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM app_settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default

    def set_app_setting(self, key: str, value: str):
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO app_settings (key, value) VALUES (?, ?)
                   ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
                (key, value),
            )
            conn.commit()

    # ═════════════════════════════════════════════
    # Projects
    # ═════════════════════════════════════════════
    def list_projects(self) -> List[Project]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM projects ORDER BY is_default DESC, id"
            ).fetchall()
            return [row_to_model(r, Project) for r in rows]

    def get_project(self, project_id: int) -> Optional[Project]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
            return row_to_model(row, Project) if row else None

    def get_project_by_name(self, name: str) -> Optional[Project]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE name = ?", (name,)
            ).fetchone()
            return row_to_model(row, Project) if row else None

    def create_project(self, name: str, fa_name: str = "",
                       description: str = "") -> Project:
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO projects (name, fa_name, description)
                   VALUES (?, ?, ?)""",
                (name, fa_name, description),
            )
            conn.commit()
            return Project(
                id=cursor.lastrowid,
                name=name, fa_name=fa_name, description=description,
            )

    def update_project(self, project: Project) -> bool:
        with self._connect() as conn:
            conn.execute(
                """UPDATE projects
                   SET name = ?, fa_name = ?, description = ?, db_name = ?
                   WHERE id = ?""",
                (project.name, project.fa_name, project.description,
                 getattr(project, "db_name", ""), project.id),
            )
            conn.commit()
            return True

    def delete_project(self, project_id: int) -> bool:
        with self._connect() as conn:
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            return True

    def project_exists(self, name: str, exclude_id: int | None = None) -> bool:
        with self._connect() as conn:
            if exclude_id:
                row = conn.execute(
                    "SELECT id FROM projects WHERE name = ? AND id != ?",
                    (name, exclude_id),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT id FROM projects WHERE name = ?", (name,)
                ).fetchone()
            return row is not None

    # ═════════════════════════════════════════════
    # Active Project
    # ═════════════════════════════════════════════
    def get_or_create_default_project(self) -> Project:
        """دریافت یا ساخت پروژه‌ی پیش‌فرض"""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE name = 'default'"
            ).fetchone()

            if row:
                return row_to_model(row, Project)

            cursor = conn.execute(
                """INSERT INTO projects (name, fa_name, description, is_default)
                   VALUES (?, ?, ?, ?)""",
                ("default", "پروژه‌ی پیش‌فرض", "پروژه‌ی پیش‌فرض", 1),
            )
            conn.commit()
            return Project(
                id=cursor.lastrowid,
                name="default", fa_name="پروژه‌ی پیش‌فرض",
                description="پروژه‌ی پیش‌فرض",
            )

    def get_active_project(self) -> Project:
        """دریافت پروژه‌ی فعال (یا ساخت پیش‌فرض)"""
        active_id_str = self.get_app_setting("active_project_id", "")

        if active_id_str:
            try:
                active_id = int(active_id_str)
                project = self.get_project(active_id)
                if project:
                    return project
            except ValueError:
                pass

        # fallback: پروژه‌ی پیش‌فرض
        project = self.get_or_create_default_project()
        self.set_active_project(project.id)
        return project

    def set_active_project(self, project_id: int):
        """تنظیم پروژه‌ی فعال"""
        self.set_app_setting("active_project_id", str(project_id))

    # ═════════════════════════════════════════════
    # Project Stats
    # ═════════════════════════════════════════════
    def project_stats(self, project_id: int) -> dict:
        """آمار پروژه"""
        with self._connect() as conn:
            tables = conn.execute(
                "SELECT COUNT(*) as c FROM custom_tables WHERE project_id = ?",
                (project_id,),
            ).fetchone()["c"]

            groups = conn.execute(
                "SELECT COUNT(*) as c FROM table_groups WHERE project_id = ?",
                (project_id,),
            ).fetchone()["c"]

            columns = conn.execute(
                """SELECT COUNT(*) as c FROM custom_columns
                   WHERE table_id IN
                   (SELECT id FROM custom_tables WHERE project_id = ?)""",
                (project_id,),
            ).fetchone()["c"]

            return {"tables": tables, "groups": groups, "columns": columns}

    # ═════════════════════════════════════════════
    # Groups
    # ═════════════════════════════════════════════
    def list_groups(self, project_id: int) -> List[TableGroup]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM table_groups WHERE project_id = ? "
                "ORDER BY order_index, id",
                (project_id,),
            ).fetchall()

            groups = []
            for r in rows:
                d = dict(r)
                if "is_default" in d:
                    d["is_default"] = bool(d["is_default"])
                valid = {f.name for f in dataclasses.fields(TableGroup)}
                groups.append(TableGroup(**{k: v for k, v in d.items() if k in valid}))
            return groups

    def get_group(self, group_id: int) -> Optional[TableGroup]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM table_groups WHERE id = ?", (group_id,)
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            if "is_default" in d:
                d["is_default"] = bool(d["is_default"])
            return row_to_model(row, TableGroup)

    def save_group(self, group: TableGroup) -> TableGroup:
        with self._connect() as conn:
            if group.id is None:
                cursor = conn.execute(
                    """INSERT INTO table_groups
                       (project_id, name, fa_name, color, icon,
                        order_index, is_default)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (group.project_id, group.name, group.fa_name,
                     group.color, group.icon, group.order_index,
                     int(group.is_default)),
                )
                group.id = cursor.lastrowid
            else:
                conn.execute(
                    """UPDATE table_groups
                       SET name = ?, fa_name = ?, color = ?,
                           icon = ?, order_index = ?, is_default = ?
                       WHERE id = ?""",
                    (group.name, group.fa_name, group.color,
                     group.icon, group.order_index, int(group.is_default),
                     group.id),
                )
            conn.commit()
            return group

    def delete_group(self, group_id: int) -> bool:
        with self._connect() as conn:
            conn.execute("DELETE FROM table_groups WHERE id = ?", (group_id,))
            conn.commit()
            return True

    # ═════════════════════════════════════════════
    # Tables
    # ═════════════════════════════════════════════
    def list_tables(self, project_id: int,
                    group_id: Optional[int] = None) -> List[CustomTable]:
        with self._connect() as conn:
            if group_id is not None:
                rows = conn.execute(
                    "SELECT * FROM custom_tables WHERE project_id = ? "
                    "AND group_id = ? ORDER BY order_index, id",
                    (project_id, group_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM custom_tables WHERE project_id = ? "
                    "ORDER BY order_index, id",
                    (project_id,),
                ).fetchall()

            tables = []
            for row in rows:
                t = row_to_model(row, CustomTable)
                t.columns = self._load_columns(conn, t.id)
                tables.append(t)
            return tables

    def get_table(self, table_id: int) -> Optional[CustomTable]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM custom_tables WHERE id = ?", (table_id,)
            ).fetchone()
            if not row:
                return None
            t = row_to_model(row, CustomTable)
            t.columns = self._load_columns(conn, t.id)
            return t

    def _load_columns(self, conn, table_id: int) -> List[CustomColumn]:
        rows = conn.execute(
            "SELECT * FROM custom_columns WHERE table_id = ? "
            "ORDER BY order_index, id",
            (table_id,),
        ).fetchall()

        columns = []
        for r in rows:
            d = dict(r)
            for key in ("allow_null", "is_primary", "is_unique",
                        "is_auto_increment", "is_searchable"):
                if key in d:
                    d[key] = bool(d[key])
            valid = {f.name for f in dataclasses.fields(CustomColumn)}
            columns.append(CustomColumn(**{k: v for k, v in d.items() if k in valid}))
        return columns

    def save_table(self, table: CustomTable) -> CustomTable:
        with self._connect() as conn:
            if table.id is None:
                cursor = conn.execute(
                    """INSERT INTO custom_tables
                       (project_id, group_id, name, fa_name, description,
                        is_default, order_index)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (table.project_id, table.group_id, table.name,
                     table.fa_name, table.description,
                     int(table.is_default), table.order_index),
                )
                table.id = cursor.lastrowid
            else:
                conn.execute(
                    """UPDATE custom_tables
                       SET group_id = ?, name = ?, fa_name = ?,
                           description = ?, is_default = ?, order_index = ?
                       WHERE id = ?""",
                    (table.group_id, table.name, table.fa_name,
                     table.description, int(table.is_default),
                     table.order_index, table.id),
                )
                conn.execute(
                    "DELETE FROM custom_columns WHERE table_id = ?", (table.id,)
                )

            for i, col in enumerate(table.columns):
                col.table_id = table.id
                col.order_index = i
                conn.execute(
                    """INSERT INTO custom_columns
                       (table_id, name, fa_name, data_type, allow_null,
                        default_value, is_primary, is_unique, is_auto_increment,
                        is_searchable, comment, order_index)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (col.table_id, col.name, col.fa_name, col.data_type,
                     int(col.allow_null), col.default_value,
                     int(col.is_primary), int(col.is_unique),
                     int(col.is_auto_increment), int(col.is_searchable),
                     col.comment, col.order_index),
                )

            conn.commit()
            return table

    def delete_table(self, table_id: int) -> bool:
        with self._connect() as conn:
            conn.execute("DELETE FROM custom_tables WHERE id = ?", (table_id,))
            conn.commit()
            return True

    def clear_project(self, project_id: int):
        """پاک کردن جداول و گروه‌های یه پروژه (پروژه بمونه)"""
        with self._connect() as conn:
            conn.execute("DELETE FROM custom_tables WHERE project_id = ?",
                         (project_id,))
            conn.execute("DELETE FROM table_groups WHERE project_id = ?",
                         (project_id,))
            conn.commit()

    # ═════════════════════════════════════════════
    # Project Settings
    # ═════════════════════════════════════════════
    def get_setting(self, project_id: int, key: str, default: str = "") -> str:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM project_settings WHERE project_id = ? AND key = ?",
                (project_id, key),
            ).fetchone()
            return row["value"] if row else default

    def set_setting(self, project_id: int, key: str, value: str):
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO project_settings (project_id, key, value)
                   VALUES (?, ?, ?)
                   ON CONFLICT(project_id, key) DO UPDATE SET value = excluded.value""",
                (project_id, key, value),
            )
            conn.commit()

    # ═════════════════════════════════════════════
    # Export
    # ═════════════════════════════════════════════
    def export_project(self, project_id: int) -> dict:
        project = self.get_project(project_id)
        groups = self.list_groups(project_id)
        tables = self.list_tables(project_id)

        return {
            "project": project.to_dict() if project else None,
            "groups": [g.to_dict() for g in groups],
            "tables": [t.to_dict() for t in tables],
        }