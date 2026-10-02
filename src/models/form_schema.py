# src/models/form_schema.py
"""
مدل داده‌ای Form Builder بصری
─────────────────────────────────
• FieldElement   → فیلد روی Canvas (با visible / searchable / auto_fill)
• ActionButton   → دکمه روی Canvas (با endpoint / method / payload_fields)
• FormPage       → کل فرم + متد payload_for_action()
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Optional


# ═══════════════════════════════════════════════════════════
# نقشه‌برداری نوع دیتابیس → نوع ویجت
# ═══════════════════════════════════════════════════════════
def map_type_to_widget(col_type: str) -> str:
    """تبدیل نوع ستون دیتابیس به نوع ویجت UI"""
    t = (col_type or "").lower()
    if "bigint" in t or "int" in t:
        return "number"
    if "bool" in t or "tinyint(1)" in t:
        return "checkbox"
    if "timestamp" in t or "datetime" in t:
        return "datetime"
    if "date" in t:
        return "date"
    if "time" in t:
        return "time"
    if "text" in t or "blob" in t:
        return "textarea"
    if "enum" in t:
        return "dropdown"
    return "textfield"


# ═══════════════════════════════════════════════════════════
# تشخیص خودکار پر شدن (auto_fill)
# ═══════════════════════════════════════════════════════════
def guess_auto_fill(col_type: str, col_name: str,
                    default=None, extra: str = "") -> Optional[str]:
    """تشخیص خودکار پر شدن فیلد"""
    t = (col_type or "").lower()
    name = (col_name or "").lower()
    d = str(default or "").upper()
    e = (extra or "").lower()

    if "auto_increment" in e:
        return "auto_increment"

    if "timestamp" in t or "datetime" in t:
        if "on update" in e:
            return "now_on_update"
        if "CURRENT_TIMESTAMP" in d:
            return "now"
        if name in ("created_at", "assigned_at", "inserted_at"):
            return "now"
        if name in ("updated_at", "modified_at", "changed_at"):
            return "now_on_update"

    if name in ("created_by", "owner_id", "creator_id"):
        return "current_user"

    if "uuid" in t or name.endswith("_uuid"):
        return "uuid"

    return None


def auto_fill_label(auto: Optional[str]) -> str:
    """برچسب فارسی برای نمایش در UI"""
    return {
        "now":             "⚡ الان",
        "now_on_update":   "⚡ در هر ویرایش",
        "auto_increment":  "⚡ خودکار (DB)",
        "current_user":    "⚡ کاربر جاری",
        "uuid":            "⚡ UUID خودکار",
    }.get(auto, "")


# ═══════════════════════════════════════════════════════════
# FieldElement — فیلد روی Canvas
# ═══════════════════════════════════════════════════════════
@dataclass
class FieldElement:
    id: str
    table: str
    column: str
    label: str
    widget_type: str
    x: int
    y: int
    width: int = 260
    height: int = 32
    required: bool = False
    validators: dict = field(default_factory=dict)
    auto_fill: Optional[str] = None
    visible: bool = True
    searchable: bool = False

    @staticmethod
    def create(table: str, column: str, col_type: str,
               x: int, y: int,
               default=None, extra: str = "") -> "FieldElement":
        widget = map_type_to_widget(col_type)
        auto = guess_auto_fill(col_type, column, default, extra)

        return FieldElement(
            id=str(uuid.uuid4())[:8],
            table=table,
            column=column,
            label=column.replace("_", " ").title(),
            widget_type=widget,
            x=x, y=y,
            auto_fill=auto,
            required=(auto is None),
            visible=True,
            searchable=False,
        )


# ═══════════════════════════════════════════════════════════
# ActionButton — دکمه روی Canvas
# ═══════════════════════════════════════════════════════════
@dataclass
class ActionButton:
    id: str
    label: str
    action: str               # create / read / update / delete / search / custom
    method: str               # POST / GET / PUT / DELETE
    endpoint: str
    order: int = 0
    x: int = 0
    y: int = 0
    width: int = 120
    height: int = 40
    enabled: bool = True
    description: str = ""
    payload_fields: List[str] = field(default_factory=list)

    # ═══════════════════════════════════════════════════════
    # ⭐ این متد گم شده بود
    # ═══════════════════════════════════════════════════════
    @staticmethod
    def default_set(table: str) -> List["ActionButton"]:
        """دکمه‌های پیش‌فرض — حالا خالی (کاربر از پنل CRUD اضافه می‌کنه)"""
        return []

# ═══════════════════════════════════════════════════════════
# متادیتای اقدام‌ها
# ═══════════════════════════════════════════════════════════
ACTION_META = {
    "create": {
        "icon": "➕", "label_fa": "ثبت",
        "method": "POST",
        "endpoint_tpl": "/api/{table}",
        "default_payload": "visible_no_pk_auto",
    },
    "read": {
        "icon": "👁", "label_fa": "نمایش",
        "method": "GET",
        "endpoint_tpl": "/api/{table}",
        "default_payload": "none",
    },
    "update": {
        "icon": "✏️", "label_fa": "ویرایش",
        "method": "PUT",
        "endpoint_tpl": "/api/{table}/{id}",
        "default_payload": "all_visible",
    },
    "delete": {
        "icon": "🗑", "label_fa": "حذف",
        "method": "DELETE",
        "endpoint_tpl": "/api/{table}/{id}",
        "default_payload": "pk_only",
    },
    "search": {
        "icon": "🔍", "label_fa": "جستجو",
        "method": "GET",
        "endpoint_tpl": "/api/{table}/search",
        "default_payload": "searchable_only",
    },
    "custom": {
        "icon": "⚙️", "label_fa": "دلخواه",
        "method": "POST",
        "endpoint_tpl": "/api/{table}",
        "default_payload": "none",
    },
}


def action_meta(action_key: str) -> dict:
    """متادیتای یک اکشن"""
    return ACTION_META.get(action_key, ACTION_META["custom"])


# ═══════════════════════════════════════════════════════════
# FormPage — کل فرم
# ═══════════════════════════════════════════════════════════
@dataclass
class FormPage:
    id: str
    name: str
    table: str
    fields: List[FieldElement] = field(default_factory=list)
    buttons: List[ActionButton] = field(default_factory=list)

    @staticmethod
    def create(name: str, table: str) -> "FormPage":
        return FormPage(
            id=str(uuid.uuid4())[:8],
            name=name,
            table=table,
            buttons=[],   # ⭐ خالی
        )

    # ─── سریالایز ───
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "table": self.table,
            "fields": [asdict(f) for f in self.fields],
            "buttons": [asdict(b) for b in self.buttons],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    # ─── کمکی ───
    def find_field(self, field_id: str) -> Optional[FieldElement]:
        for f in self.fields:
            if f.id == field_id:
                return f
        return None

    def find_field_by_column(self, column: str) -> Optional[FieldElement]:
        for f in self.fields:
            if f.column == column:
                return f
        return None

    def find_button(self, btn_id: str) -> Optional[ActionButton]:
        for b in self.buttons:
            if b.id == btn_id:
                return b
        return None

    def remove_field(self, field_id: str) -> bool:
        for i, f in enumerate(self.fields):
            if f.id == field_id:
                del self.fields[i]
                return True
        return False

    def remove_button(self, btn_id: str) -> bool:
        for i, b in enumerate(self.buttons):
            if b.id == btn_id:
                del self.buttons[i]
                return True
        return False

    def reorder_buttons(self):
        for i, b in enumerate(sorted(self.buttons, key=lambda x: x.order)):
            b.order = i

    # ─── payload خودکار ───
    def payload_for_action(self, action: ActionButton,
                           values: dict | None = None) -> dict:
        values = values or {}
        payload_fields: List[str] = []

        if action.payload_fields:
            payload_fields = action.payload_fields
        else:
            meta = action_meta(action.action)
            strategy = meta.get("default_payload", "none")
            payload_fields = self._resolve_payload_fields(strategy)

        result = {}
        for col_name in payload_fields:
            f = self.find_field_by_column(col_name)
            if f is None:
                continue

            if col_name in values:
                result[col_name] = values[col_name]
            elif f.auto_fill:
                result[col_name] = f"<auto:{f.auto_fill}>"
            else:
                result[col_name] = f"<{f.widget_type}>"

        return result

    def _resolve_payload_fields(self, strategy: str) -> List[str]:
        fields = self.fields
        pk_names = self._primary_key_names()

        if strategy == "none":
            return []
        if strategy == "pk_only":
            return [f.column for f in fields if f.column in pk_names]
        if strategy == "all_visible":
            return [f.column for f in fields if f.visible]
        if strategy == "visible_no_pk_auto":
            return [
                f.column for f in fields
                if f.visible
                and f.column not in pk_names
                and f.auto_fill is None
            ]
        if strategy == "searchable_only":
            return [f.column for f in fields if f.searchable]
        return []

    def _primary_key_names(self) -> set:
        likely = {"id", "uuid"}
        result = set()
        for f in self.fields:
            if f.column.lower() in likely:
                result.add(f.column)
            if f.auto_fill == "auto_increment":
                result.add(f.column)
        return result

    def suggested_payload_fields(self, action: ActionButton) -> List[str]:
        if action.payload_fields:
            return list(action.payload_fields)
        meta = action_meta(action.action)
        strategy = meta.get("default_payload", "none")
        return self._resolve_payload_fields(strategy)