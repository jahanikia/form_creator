# src/views/main_view/sections/body.py
"""BodySection — بدنه‌ی اصلی (ساده، بدون CRUD)"""

import customtkinter as ctk


BG_PANEL  = "#232323"
BG_LIST   = "#1a1a1a"
BG_DETAIL = "#1e1e1e"
ROW_BG    = "#2e2e2e"
ROW_SEL   = "#0d6efd"
ROW_HOV   = "#3a3a3a"


class BodySection(ctk.CTkFrame):
    """بدنه اصلی"""

    def __init__(self, master, on_table_select=None):
        super().__init__(master, fg_color="transparent")
        self.on_table_select = on_table_select
        self.current_table: str | None = None
        self._row_widgets: dict[str, ctk.CTkButton] = {}

        self.grid_columnconfigure(0, weight=0, minsize=240)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_table_list()
        self._build_detail()

    def _build_table_list(self):
        panel = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=8)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        header = ctk.CTkFrame(panel, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            header, text="📋 جداول",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        self.tables_count_lbl = ctk.CTkLabel(
            header, text="(0)",
            text_color="#888",
            font=ctk.CTkFont(size=11),
        )
        self.tables_count_lbl.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(
            panel,
            text="برای مشاهده جزئیات کلیک کنید",
            text_color="#666",
            font=ctk.CTkFont(size=10),
        ).pack(anchor="w", padx=14, pady=(0, 6))

        self.table_list = ctk.CTkScrollableFrame(panel, fg_color=BG_LIST)
        self.table_list.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.empty_lbl = ctk.CTkLabel(
            self.table_list,
            text="\n\n🔌  ابتدا به دیتابیس متصل شوید",
            text_color="#666",
            font=ctk.CTkFont(size=12),
        )
        self.empty_lbl.pack(pady=20)

    def _build_detail(self):
        self.detail = ctk.CTkFrame(self, fg_color=BG_DETAIL, corner_radius=8)
        self.detail.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.detail_empty = ctk.CTkLabel(
            self.detail,
            text="\n\n\n📊\n\nیک جدول از سمت چپ انتخاب کنید\n"
                 "تا ستون‌های آن نمایش داده شود",
            text_color="#666",
            font=ctk.CTkFont(size=14),
            justify="center",
        )
        self.detail_empty.pack(expand=True)

    # ═════════════════════════════════════════════
    def load_tables(self, tables: list[str]):
        for w in self.table_list.winfo_children():
            w.destroy()
        self._row_widgets.clear()

        if not tables:
            ctk.CTkLabel(
                self.table_list,
                text="\n\nهیچ جدولی یافت نشد",
                text_color="#666",
                font=ctk.CTkFont(size=12),
            ).pack(pady=20)
            self.tables_count_lbl.configure(text="(0)")
            return

        for t in tables:
            self._add_table_row(t)

        self.tables_count_lbl.configure(text=f"({len(tables)})")

    def _add_table_row(self, table_name: str):
        btn = ctk.CTkButton(
            self.table_list,
            text=f"📋  {table_name}",
            anchor="w", height=38,
            fg_color=ROW_BG, hover_color=ROW_HOV,
            font=ctk.CTkFont(size=12),
            command=lambda t=table_name: self._on_click(t),
        )
        btn.pack(fill="x", pady=3, padx=2)
        self._row_widgets[table_name] = btn

    def _on_click(self, table_name: str):
        for name, btn in self._row_widgets.items():
            btn.configure(
                fg_color=ROW_SEL if name == table_name else ROW_BG,
                hover_color="#0b5ed7" if name == table_name else ROW_HOV,
            )

        self.current_table = table_name
        if self.on_table_select:
            self.on_table_select(table_name)

    def show_columns(self, table_name: str, columns: list[dict]):
        for w in self.detail.winfo_children():
            w.destroy()

        header = ctk.CTkFrame(self.detail, fg_color="#252525", height=50, corner_radius=6)
        header.pack(fill="x", padx=12, pady=(12, 6))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text=f"📊  {table_name}",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left", padx=14)

        ctk.CTkLabel(
            header, text=f"{len(columns)} ستون",
            text_color="#888", font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=8)

        cols_frame = ctk.CTkScrollableFrame(self.detail, fg_color="#151515")
        cols_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        cols_header = ctk.CTkFrame(cols_frame, fg_color="#2a2a2a", corner_radius=4)
        cols_header.pack(fill="x", pady=(0, 4))

        for text, w in [("نام ستون", 180), ("نوع داده", 220),
                        ("Nullable", 90), ("کلید", 70)]:
            ctk.CTkLabel(
                cols_header, text=text, width=w, anchor="w",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#9ecbff",
            ).pack(side="left", padx=8, pady=8)

        KEY_ICONS = {"PRI": "🔑", "UNI": "⭐", "MUL": "🔗"}

        for i, col in enumerate(columns):
            bg = "#1e1e1e" if i % 2 == 0 else "#232323"
            row = ctk.CTkFrame(cols_frame, fg_color=bg, corner_radius=4)
            row.pack(fill="x", pady=1)

            ctk.CTkLabel(
                row, text=col["name"], width=180, anchor="w",
                font=ctk.CTkFont(size=12),
            ).pack(side="left", padx=8, pady=6)

            ctk.CTkLabel(
                row, text=col["type"], width=220, anchor="w",
                font=ctk.CTkFont(size=11), text_color="#bbb",
            ).pack(side="left", padx=8)

            nullable = "YES" if col.get("nullable") else "NO"
            ctk.CTkLabel(
                row, text=nullable, width=90, anchor="w",
                font=ctk.CTkFont(size=11),
                text_color="#7bd88f" if nullable == "YES" else "#c97a7a",
            ).pack(side="left", padx=8)

            key_icon = KEY_ICONS.get(col.get("key", ""), "—")
            ctk.CTkLabel(
                row, text=key_icon, width=70,
                font=ctk.CTkFont(size=14),
            ).pack(side="left", padx=8)

    def clear_detail(self):
        for w in self.detail.winfo_children():
            w.destroy()

        self.detail_empty = ctk.CTkLabel(
            self.detail,
            text="\n\n\n📊\n\nیک جدول از سمت چپ انتخاب کنید",
            text_color="#666", font=ctk.CTkFont(size=14),
            justify="center",
        )
        self.detail_empty.pack(expand=True)