# src/views/form_builder/sections/table_panel.py
"""
پنل لیست جداول
─────────────────────────────────
سمت چپ پنجره — کاربر یکی رو انتخاب می‌کنه
و ستون‌های اون جدول بارگذاری می‌شن.
"""

import customtkinter as ctk


# رنگ‌بندی
BG_PANEL     = "#232323"
BG_LIST      = "#1a1a1a"
BTN_NORMAL   = "#2e2e2e"
BTN_HOVER    = "#3a3a3a"
BTN_SELECTED = "#0d6efd"
BTN_SEL_HOV  = "#0b5ed7"


class TablePanel(ctk.CTkFrame):
    """پنل لیست جداول"""

    def __init__(self, master, tables: list[str], on_select=None):
        super().__init__(master, fg_color=BG_PANEL, corner_radius=8)
        self.on_select = on_select
        self.current_table: str | None = None
        self._row_widgets: dict[str, ctk.CTkButton] = {}

        # ─── هدر ───
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkLabel(
            header,
            text="📋 جداول",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=f"({len(tables)})",
            text_color="#888",
            font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=(6, 0))

        ctk.CTkLabel(
            self,
            text="برای بارگذاری ستون‌ها کلیک کنید",
            text_color="#777",
            font=ctk.CTkFont(size=10),
        ).pack(anchor="w", padx=12, pady=(0, 6))

        # ─── لیست جداول ───
        self.listbox = ctk.CTkScrollableFrame(self, fg_color=BG_LIST)
        self.listbox.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        for t in tables:
            self._add_row(t)

    # ─────────────────────────────────────────────
    def _add_row(self, table_name: str):
        btn = ctk.CTkButton(
            self.listbox,
            text=f"📋  {table_name}",
            anchor="w",
            height=38,
            fg_color=BTN_NORMAL,
            hover_color=BTN_HOVER,
            font=ctk.CTkFont(size=12),
            command=lambda t=table_name: self._on_click(t),
        )
        btn.pack(fill="x", pady=3, padx=2)
        self._row_widgets[table_name] = btn

    def _on_click(self, table_name: str):
        # ریست کردن رنگ‌ها
        for name, btn in self._row_widgets.items():
            btn.configure(
                fg_color=BTN_SELECTED if name == table_name else BTN_NORMAL,
                hover_color=BTN_SEL_HOV if name == table_name else BTN_HOVER,
            )

        self.current_table = table_name

        if self.on_select:
            self.on_select(table_name)