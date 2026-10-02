# src/services/schema_seeder.py
"""
Seeder — ریختن جداول و گروه‌های پیش‌فرض در SQLite
─────────────────────────────────
"""

from src.services.schema_store import SchemaStore
from src.services.default_schema import (
    get_default_tables,
    get_default_groups,
    table_default_group,
    DEFAULT_TABLE_NAMES,
)


class SchemaSeeder:
    """پرکردن پایگاه‌داده با داده‌های پیش‌فرض"""

    def __init__(self, store: SchemaStore):
        self.store = store

    # ═════════════════════════════════════════════
    def seed_if_empty(self, project_id: int) -> dict:
        """اگه خالیه، همه‌چیز رو بریز"""
        existing = self.store.list_tables(project_id)
        if existing:
            return {"groups": 0, "tables": 0}
        return self.force_seed(project_id)

    # ═════════════════════════════════════════════
    def force_seed(self, project_id: int) -> dict:
        """گروه‌ها + جداول پیش‌فرض"""
        # ─── گروه‌ها ───
        groups = get_default_groups(project_id)
        group_map = {}
        for g in groups:
            saved = self.store.save_group(g)
            group_map[saved.name] = saved.id

        # ─── جداول ───
        tables = get_default_tables(project_id)
        for t in tables:
            group_name = table_default_group(t.name)
            t.group_id = group_map.get(group_name)
            self.store.save_table(t)

        return {"groups": len(groups), "tables": len(tables)}

    # ═════════════════════════════════════════════
    def add_missing_defaults(self, project_id: int) -> dict:
        """فقط موارد گم‌شده"""
        existing_groups = {g.name: g for g in self.store.list_groups(project_id)}
        group_map = {name: g.id for name, g in existing_groups.items()}

        added_groups = 0
        for g in get_default_groups(project_id):
            if g.name not in existing_groups:
                saved = self.store.save_group(g)
                group_map[saved.name] = saved.id
                added_groups += 1

        existing_names = {t.name for t in self.store.list_tables(project_id)}
        added_tables = 0
        for t in get_default_tables(project_id):
            if t.name not in existing_names:
                group_name = table_default_group(t.name)
                t.group_id = group_map.get(group_name)
                self.store.save_table(t)
                added_tables += 1

        return {"groups": added_groups, "tables": added_tables}

    # ═════════════════════════════════════════════
    def reset_to_defaults(self, project_id: int) -> dict:
        """ریست کامل"""
        self.store.clear_project(project_id)
        return self.force_seed(project_id)