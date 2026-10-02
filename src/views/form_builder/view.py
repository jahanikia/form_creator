# src/views/form_builder/view.py
"""
پنجره Form Builder — Visual Designer
─────────────────────────────────
• چپ: لیست جداول + پنل CRUD
• وسط: Canvas
• راست: ستون‌ها (بالا) + کتابخانه دکمه‌ها (پایین)
• پایین: نوار عملیات
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog

from src.models.form_schema import FormPage, ActionButton, action_meta
from src.services.mock_schema import list_tables, get_columns
from src.services.mock_api import MockApiClient

from .sections import (
    TablePanel,
    ColumnPanel,
    FormCanvas,
    ButtonsLibrary,
)


BG_WINDOW = "#1a1a1a"

# ─── رنگ‌های CRUD ───
CRUD_COLORS = {
    "create": "#198754",
    "read":   "#0d6efd",
    "update": "#fd7e14",
    "delete": "#dc3545",
}
CRUD_ICONS = {
    "create": "➕",
    "read":   "👁",
    "update": "✏️",
    "delete": "🗑",
}


class FormBuilderView(ctk.CTkToplevel):
    """پنجره‌ی اصلی Form Builder"""

    HISTORY_LIMIT = 20

    def __init__(self, master=None, on_close=None):
        super().__init__(master)
        
        from src.services.schema_store import SchemaStore
        _store = SchemaStore()
        self.project = _store.get_active_project()        
        
        self.on_close = on_close

        self.title("🎨 Form Builder — Visual Designer")
        self.geometry("1450x850")
        self.minsize(1200, 700)
        self.configure(fg_color=BG_WINDOW)

        # ═══ State ═══
        self.api = MockApiClient()
        self.form_page: FormPage = FormPage.create("users_form", "users")
        self._history: list[FormPage] = []
        self._history_index: int = -1

        # ═══ Layout ═══
        self._build_layout()

        # ═══ انتخاب اولیه (بعد از layout) ═══
        self._on_table_select("users", push_history=True)

        self.after(50, self.focus_force)
        self.protocol("WM_DELETE_WINDOW", self._close_and_return)

    # ═════════════════════════════════════════════
    # ساخت Layout
    # ═════════════════════════════════════════════
    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0, minsize=240)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0, minsize=340)
        self.grid_rowconfigure(0, weight=1)

        # ⭐ اول نوار پایین (تا back_btn قبل از هر push_history آماده باشه)
        self._build_bottom_bar()

        # ═══ چپ: جداول + CRUD ═══
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=(10, 5))
        left.grid_rowconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=0)
        left.grid_columnconfigure(0, weight=1)

        # ─── لیست جداول ───
        self.table_panel = TablePanel(
            left,
            tables=list_tables(),
            on_select=lambda t: self._on_table_select(t, push_history=True),
        )
        self.table_panel.grid(row=0, column=0, sticky="nsew")

        # ─── پنل CRUD ───
        self.crud_panel = self._build_crud_panel(left)
        self.crud_panel.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        # ═══ وسط: Canvas ═══
        self.canvas_area = FormCanvas(
            self,
            self.form_page,
            on_fields_change=self._on_fields_change,
        )
        self.canvas_area.grid(row=0, column=1, sticky="nsew", padx=5, pady=(10, 5))

        # ═══ راست: ستون‌ها + کتابخانه ═══
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=(10, 5))
        right.grid_rowconfigure(0, weight=2)
        right.grid_rowconfigure(1, weight=3)
        right.grid_columnconfigure(0, weight=1)

        # ⭐ on_add_field → add_field_from_column (اسم واقعی متد)
        self.column_panel = ColumnPanel(
            right,
            on_add_field=self.add_field_from_column,
        )
        self.column_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 8))

        self.buttons_library = ButtonsLibrary(
            right,
            form_page=self.form_page,
            on_run=self._run_chain,
            on_canvas_refresh=self._on_buttons_change,
        )
        self.buttons_library.grid(row=1, column=0, sticky="nsew")

    # ═════════════════════════════════════════════
    # پنل CRUD
    # ═════════════════════════════════════════════
    def _build_crud_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="#232323", corner_radius=8)

        header = ctk.CTkFrame(panel, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkLabel(
            header,
            text="⚡ اکشن‌های سریع",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#9ecbff",
        ).pack(side="left")

        self.crud_table_lbl = ctk.CTkLabel(
            header, text="—", text_color="#888",
            font=ctk.CTkFont(size=10),
        )
        self.crud_table_lbl.pack(side="right")

        ctk.CTkLabel(
            panel,
            text="افزودن/حذف دکمه روی Canvas",
            text_color="#666", font=ctk.CTkFont(size=9),
        ).pack(anchor="w", padx=12, pady=(0, 4))

        btns = ctk.CTkFrame(panel, fg_color="transparent")
        btns.pack(fill="x", padx=8, pady=(0, 6))

        self.crud_buttons = {}

        for i, (key, label) in enumerate([
            ("create", "ثبت"),
            ("read",   "نمایش"),
            ("update", "ویرایش"),
            ("delete", "حذف"),
        ]):
            btn = ctk.CTkButton(
                btns,
                text=f"{CRUD_ICONS[key]} {label}",
                height=32,
                fg_color=CRUD_COLORS[key],
                hover_color=self._darker(CRUD_COLORS[key]),
                font=ctk.CTkFont(size=11),
                command=lambda k=key: self._on_quick_crud(k),
            )
            btn.grid(row=i // 2, column=i % 2, sticky="ew", padx=2, pady=2)
            self.crud_buttons[key] = btn

        btns.grid_columnconfigure(0, weight=1)
        btns.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            panel,
            text="🎨  افزودن همه به Canvas",
            height=30,
            fg_color="#6f42c1", hover_color="#5a32a3",
            font=ctk.CTkFont(size=11),
            command=self._on_quick_add_all,
        ).pack(fill="x", padx=8, pady=(0, 8))

        return panel

    # ═════════════════════════════════════════════
    # نوار پایین
    # ═════════════════════════════════════════════
    def _build_bottom_bar(self):
        bar = ctk.CTkFrame(self, fg_color="#181818", height=56, corner_radius=6)
        bar.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=(5, 10))
        bar.grid_propagate(False)

        # ⭐ نام پروژه
        self.project_lbl = ctk.CTkLabel(
            bar,
            text=f"📦 {self.project.fa_name or self.project.name}",
            text_color="#fd7e14",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.project_lbl.pack(side="left", padx=(14, 8), pady=10)

        # جداکننده
        ctk.CTkFrame(
            bar, fg_color="#444", width=1, height=28, corner_radius=0,
        ).pack(side="left", padx=6, pady=14)

        ctk.CTkButton(
            bar, text="🏠  فرم اصلی",
            width=130,
            fg_color="#dc3545", hover_color="#b02a37",
            command=self._close_and_return,
        ).pack(side="left", padx=(10, 6), pady=10)

        self.back_btn = ctk.CTkButton(
            bar, text="⬅  فرم قبلی",
            width=130,
            fg_color="#6f42c1", hover_color="#5a32a3",
            command=self._go_back,
        )
        self.back_btn.pack(side="left", padx=6, pady=10)

        ctk.CTkButton(
            bar, text="💾  ذخیره Schema",
            width=140,
            fg_color="#0d6efd", hover_color="#0b5ed7",
            command=self._save_schema,
        ).pack(side="left", padx=6, pady=10)

        ctk.CTkButton(
            bar, text="🖨  چاپ در کنسول",
            width=140,
            fg_color="#444", hover_color="#555",
            command=self._print_schema,
        ).pack(side="left", padx=6, pady=10)

        ctk.CTkButton(
            bar, text="🧹  پاک کردن Canvas",
            width=150,
            fg_color="#6c1f1f", hover_color="#8a2828",
            command=self._clear_canvas,
        ).pack(side="left", padx=6, pady=10)

        self.status_lbl = ctk.CTkLabel(
            bar, text="آماده",
            text_color="#aaa", font=ctk.CTkFont(size=11),
        )
        self.status_lbl.pack(side="right", padx=14)

    # ═════════════════════════════════════════════
    # History
    # ═════════════════════════════════════════════
    def _push_history(self, form_page: FormPage):
        if self._history_index < len(self._history) - 1:
            self._history = self._history[: self._history_index + 1]

        self._history.append(form_page)
        if len(self._history) > self.HISTORY_LIMIT:
            self._history.pop(0)

        self._history_index = len(self._history) - 1
        self._update_back_button()

    def _go_back(self):
        if self._history_index <= 0:
            self._set_status("فرم قبلی وجود ندارد")
            return

        self._history_index -= 1
        prev_form = self._history[self._history_index]
        self._load_form(prev_form)
        self._set_status(f"⬅ بازگشت به: {prev_form.name}")
        self._update_back_button()

    def _update_back_button(self):
        if not hasattr(self, "back_btn"):
            return   # ⭐ محافظ
        if self._history_index > 0:
            prev_name = self._history[self._history_index - 1].name
            self.back_btn.configure(state="normal", text=f"⬅  {prev_name}")
        else:
            self.back_btn.configure(state="disabled", text="⬅  فرم قبلی")

    # ═════════════════════════════════════════════
    def _close_and_return(self):
        if self.form_page.fields:
            if not messagebox.askyesno(
                "بازگشت به فرم اصلی",
                "تغییرات ذخیره نشده از دست می‌رن. مطمئنی؟",
                parent=self,
            ):
                return

        if self.on_close:
            try:
                self.on_close()
            except Exception as e:
                print(f"⚠️ خطا در callback بستن: {e}")

        self.destroy()

    # ═════════════════════════════════════════════
    # رویدادها
    # ═════════════════════════════════════════════
    def _on_table_select(self, table_name: str, push_history: bool = True):
        new_form = FormPage.create(f"{table_name}_form", table_name)

        if push_history:
            self._push_history(new_form)

        self._load_form(new_form)

        if hasattr(self, "crud_table_lbl"):
            self.crud_table_lbl.configure(text=table_name)
        self._update_crud_buttons_state()

        self._set_status(f"جدول: {table_name}")

    def _load_form(self, form_page: FormPage):
        self.form_page = form_page

        self.canvas_area.set_form(form_page)
        self.buttons_library.set_form(form_page)

        columns = get_columns(form_page.table)
        self.column_panel.load_columns(form_page.table, columns)

        self._refresh_column_markers()

    # ⭐ اسم متد رو نگه می‌داریم تا callback کار کنه
    def add_field_from_column(self, table: str, col: dict):
        self.canvas_area.add_field_from_column(table, col)
        self._set_status(f"افزوده شد: {table}.{col['name']}")

    def _on_fields_change(self):
        self._refresh_column_markers()

    def _on_buttons_change(self):
        self.canvas_area.refresh_buttons()
        self._update_crud_buttons_state()

    def _refresh_column_markers(self):
        field_columns = {f.column for f in self.form_page.fields}
        self.column_panel.update_canvas_markers(field_columns)

    def _run_chain(self, form_page: FormPage):
        if not form_page.fields:
            messagebox.showwarning(
                "بدون فیلد",
                "هیچ فیلدی روی Canvas نیست!",
                parent=self,
            )
            return

        payload = {}
        for action in sorted(form_page.buttons, key=lambda a: a.order):
            if not action.enabled:
                continue
            payload = form_page.payload_for_action(action)

        self.api.run_chain(
            [b for b in form_page.buttons if b.enabled],
            payload,
        )
        self._set_status("✅ اجرای Mock انجام شد — کنسول را ببینید")

    # ═════════════════════════════════════════════
    # CRUD سریع
    # ═════════════════════════════════════════════
    @staticmethod
    def _darker(hex_color: str, factor: float = 0.75) -> str:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _on_quick_crud(self, action_key: str):
        if not self.form_page.table:
            return

        existing = next(
            (b for b in self.form_page.buttons if b.action == action_key),
            None,
        )

        if existing:
            self.form_page.remove_button(existing.id)
            self.form_page.reorder_buttons()
        else:
            import uuid
            meta = action_meta(action_key)
            endpoint = meta["endpoint_tpl"].replace("{table}", self.form_page.table)

            idx = len(self.form_page.buttons)
            new_btn = ActionButton(
                id=str(uuid.uuid4())[:8],
                label=meta["label_fa"],
                action=action_key,
                method=meta["method"],
                endpoint=endpoint,
                order=idx,
                x=30 + idx * 130,
                y=500,
                description=f"اکشن {meta['label_fa']}",
            )
            self.form_page.buttons.append(new_btn)

        self.canvas_area.refresh_buttons()
        self.buttons_library._render()
        self._update_crud_buttons_state()
        self._set_status(f"CRUD: {action_key}")

    def _on_quick_add_all(self):
        import uuid

        for key in ["create", "read", "update", "delete"]:
            if any(b.action == key for b in self.form_page.buttons):
                continue

            meta = action_meta(key)
            endpoint = meta["endpoint_tpl"].replace("{table}", self.form_page.table)

            idx = len(self.form_page.buttons)
            new_btn = ActionButton(
                id=str(uuid.uuid4())[:8],
                label=meta["label_fa"],
                action=key,
                method=meta["method"],
                endpoint=endpoint,
                order=idx,
                x=30 + idx * 130,
                y=500,
                description=f"اکشن {meta['label_fa']}",
            )
            self.form_page.buttons.append(new_btn)

        self.canvas_area.refresh_buttons()
        self.buttons_library._render()
        self._update_crud_buttons_state()
        self._set_status("همه‌ی 4 دکمه اضافه شد")

    def _update_crud_buttons_state(self):
        if not hasattr(self, "crud_buttons"):
            return

        for key, btn in self.crud_buttons.items():
            exists = any(
                b.action == key and b.enabled
                for b in self.form_page.buttons
            )
            if exists:
                btn.configure(border_width=3, border_color="#7bd88f")
            else:
                btn.configure(border_width=0)

    # ═════════════════════════════════════════════
    # ذخیره / چاپ / پاکسازی
    # ═════════════════════════════════════════════
    def _save_schema(self):
        if not self.form_page.fields:
            messagebox.showwarning("فرم خالی", "هیچ فیلدی روی Canvas نیست!", parent=self)
            return

        path = filedialog.asksaveasfilename(
            parent=self,
            title="ذخیره Schema",
            defaultextension=".json",
            initialfile=f"{self.form_page.name}.json",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return

        with open(path, "w", encoding="utf-8") as f:
            f.write(self.form_page.to_json())

        self._set_status(f"💾 ذخیره شد: {path}")
        messagebox.showinfo("ذخیره شد", f"Schema ذخیره شد در:\n{path}", parent=self)

    def _print_schema(self):
        print("\n" + "═" * 70)
        print(f"📄 SCHEMA: {self.form_page.name}")
        print("═" * 70)
        print(self.form_page.to_json())
        print("═" * 70 + "\n")
        self._set_status("🖨 Schema در کنسول چاپ شد")

    def _clear_canvas(self):
        if not self.form_page.fields and not self.form_page.buttons:
            return
        if not messagebox.askyesno(
            "پاک کردن",
            f"همه‌ی {len(self.form_page.fields)} فیلد پاک بشن؟",
            parent=self,
        ):
            return

        self.canvas_area.clear()
        self.form_page.fields.clear()
        self.canvas_area._render_all_buttons()
        self.canvas_area._update_count()
        self._refresh_column_markers()
        self._set_status("🧹 Canvas پاک شد")

    def _set_status(self, text: str):
        if hasattr(self, "status_lbl"):
            self.status_lbl.configure(text=text)