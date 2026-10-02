# src/views/form_builder/sections/column_panel.py
"""
پنل ستون‌های جدول انتخاب‌شده
─────────────────────────────────
• روی هر ستون کلیک کنی → فیلد به Canvas اضافه/حذف می‌شه
• ستون‌های روی Canvas با ✅ نشون داده می‌شن
• callback: on_add_field
"""

import customtkinter as ctk


BG_PANEL = "#232323"
BG_LIST  = "#1a1a1a"
BTN_NORM = "#2e2e2e"
BTN_HOV  = "#3a3a3a"
BTN_ON_CANVAS = "#1e4d2b"   # سبز کم‌رنگ — ستون روی Canvas هست


TYPE_ICON = {
    "number":    "🔢",
    "textfield": "🔤",
    "textarea":  "📝",
    "date":      "📅",
    "datetime":  "🕐",
    "time":      "⏱",
    "checkbox":  "☑️",
    "dropdown":  "🔽",
}


class ColumnPanel(ctk.CTkFrame):
    """پنل ستون‌ها"""

    def __init__(self, master, on_add_field=None):
        super().__init__(master, fg_color=BG_PANEL, corner_radius=8)
        self.on_add_field = on_add_field
        self.current_table: str | None = None
        self._current_columns: list[dict] = []
        self._row_widgets: dict[str, ctk.CTkButton] = {}

        # ─── هدر ───
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 4))

        self.title_lbl = ctk.CTkLabel(
            header,
            text="🔹 ستون‌ها",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.title_lbl.pack(side="left")

        self.count_lbl = ctk.CTkLabel(
            header, text="", text_color="#888",
            font=ctk.CTkFont(size=11),
        )
        self.count_lbl.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(
            self,
            text="✅ = روی Canvas  |  کلیک = افزودن/حذف",
            text_color="#777",
            font=ctk.CTkFont(size=10),
        ).pack(anchor="w", padx=12, pady=(0, 6))

        # ─── لیست ───
        self.listbox = ctk.CTkScrollableFrame(self, fg_color=BG_LIST)
        self.listbox.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.empty_lbl = ctk.CTkLabel(
            self.listbox,
            text="\n\n👈  ابتدا یک جدول انتخاب کنید",
            text_color="#666",
            font=ctk.CTkFont(size=12),
        )
        self.empty_lbl.pack(pady=20)

    # ═════════════════════════════════════════════
    def load_columns(self, table_name: str, columns: list[dict]):
        """بارگذاری ستون‌های یه جدول جدید"""
        self.current_table = table_name
        self._current_columns = columns
        self.title_lbl.configure(text=f"🔹 ستون‌های {table_name}")
        self.count_lbl.configure(text=f"({len(columns)})")

        for w in self.listbox.winfo_children():
            w.destroy()
        self._row_widgets.clear()

        for col in columns:
            self._add_column_row(col)

    def _add_column_row(self, col: dict):
        from src.models.form_schema import map_type_to_widget
        widget_type = map_type_to_widget(col["type"])
        icon = TYPE_ICON.get(widget_type, "🔹")
        badge = {"PRI": " 🔑", "UNI": " ⭐", "MUL": " 🔗"}.get(col.get("key", ""), "")

        text = f"{icon}  {col['name']}{badge}\n     {col['type']}"

        btn = ctk.CTkButton(
            self.listbox,
            text=text,
            anchor="w",
            height=48,
            fg_color=BTN_NORM,
            hover_color=BTN_HOV,
            font=ctk.CTkFont(size=11),
            command=lambda c=col: self._on_click(c),
        )
        btn.pack(fill="x", pady=3, padx=2)
        self._row_widgets[col["name"]] = btn

    def _on_click(self, col: dict):
        if self.on_add_field and self.current_table:
            self.on_add_field(self.current_table, col)

    # ⭐ آپدیت نشانگر ✅ بر اساس فیلدهای موجود در فرم
    def update_canvas_markers(self, field_columns: set[str]):
        """ستون‌هایی که روی Canvas هستن رو با ✅ نشون بده"""
        for col_name, btn in self._row_widgets.items():
            if col_name in field_columns:
                btn.configure(fg_color=BTN_ON_CANVAS)
            else:
                btn.configure(fg_color=BTN_NORM)

    def clear(self):
        for w in self.listbox.winfo_children():
            w.destroy()
        self._row_widgets.clear()
        self.current_table = None
        self._current_columns = []
        self.title_lbl.configure(text="🔹 ستون‌ها")
        self.count_lbl.configure(text="")