# src/models/form_schema.py
"""
مدل داده‌ای Form Builder بصری
─────────────────────────────────
این ماژول ساختار یک «فرم» رو تعریف می‌کنه که شامل:
  • FieldElement   → یک فیلد روی Canvas (مثلاً فیلد email)
  • ActionButton   → یک دکمه (ثبت / حذف / ویرایش / نمایش)
  • FormPage       → کل فرم (فیلدها + دکمه‌ها + متادیتا)
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import List


# ═══════════════════════════════════════════════════════════
# نقشه‌برداری نوع دیتابیس → نوع ویجت
# ═══════════════════════════════════════════════════════════
def map_type_to_widget(col_type: str) -> str:
    """تبدیل نوع ستون دیتابیس به نوع ویجت UI"""
    t = col_type.lower()
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
# FieldElement — یک فیلد روی Canvas
# ═══════════════════════════════════════════════════════════
@dataclass
class FieldElement:
    id: str
    table: str
    column: str
    label: str
    widget_type: str          # textfield / number / date / ...
    x: int                    # موقعیت افقی روی Canvas
    y: int                    # موقعیت عمودی روی Canvas
    width: int = 260
    height: int = 32
    required: bool = False
    validators: dict = field(default_factory=dict)

    @staticmethod
    def create(table: str, column: str, col_type: str, x: int, y: int) -> "FieldElement":
        """ساخت یک FieldElement از روی اطلاعات ستون دیتابیس"""
        widget = map_type_to_widget(col_type)
        return FieldElement(
            id=str(uuid.uuid4())[:8],
            table=table,
            column=column,
            label=column.replace("_", " ").title(),
            widget_type=widget,
            x=x,
            y=y,
        )


# ═══════════════════════════════════════════════════════════
# ActionButton — یک دکمه روی فرم
# ═══════════════════════════════════════════════════════════
@dataclass
class ActionButton:
    id: str
    label: str                # ثبت / حذف / ویرایش / نمایش
    action: str               # create / read / update / delete
    method: str               # POST / GET / PUT / DELETE
    endpoint: str             # /api/users
    order: int = 0            # ترتیب اجرا

    @staticmethod
    def default_set(table: str) -> List["ActionButton"]:
        """چهار دکمه‌ی پیش‌فرض CRUD برای یک جدول"""
        return [
            ActionButton(
                id=str(uuid.uuid4())[:8],
                label="ثبت", action="create", method="POST",
                endpoint=f"/api/{table}", order=0,
            ),
            ActionButton(
                id=str(uuid.uuid4())[:8],
                label="نمایش", action="read", method="GET",
                endpoint=f"/api/{table}", order=1,
            ),
            ActionButton(
                id=str(uuid.uuid4())[:8],
                label="ویرایش", action="update", method="PUT",
                endpoint=f"/api/{table}/{{id}}", order=2,
            ),
            ActionButton(
                id=str(uuid.uuid4())[:8],
                label="حذف", action="delete", method="DELETE",
                endpoint=f"/api/{table}/{{id}}", order=3,
            ),
        ]


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
        """ساخت فرم جدید با ۴ دکمه CRUD پیش‌فرض"""
        return FormPage(
            id=str(uuid.uuid4())[:8],
            name=name,
            table=table,
            buttons=ActionButton.default_set(table),
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
    def find_field(self, field_id: str) -> FieldElement | None:
        for f in self.fields:
            if f.id == field_id:
                return f
        return None

    def remove_field(self, field_id: str) -> bool:
        for i, f in enumerate(self.fields):
            if f.id == field_id:
                del self.fields[i]
                return True
        return False

    def reorder_buttons(self):
        """اطمینان از ترتیب درست order"""
        for i, b in enumerate(sorted(self.buttons, key=lambda x: x.order)):
            b.order = i