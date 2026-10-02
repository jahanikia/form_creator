# src/views/schema_designer/sections/table_list_panel.py
"""
TableListPanel — لیست جداول با گروه‌بندی
─────────────────────────────────
• درخت‌واره بر اساس گروه
• dropdown فیلتر
• جستجو
• ذخیره‌ی آخرین گروه انتخاب‌شده
"""

import customtkinter as ctk


BG_PANEL  = "#232323"
BG_LIST   = "#1a1a1a"
ROW_BG    = "#2e2e2e"
ROW_SEL   = "#0d6efd"
ROW_HOV   = "#3a3a3a"
ROW_DEFAULT = "#1e4d2b"
GROUP_HDR_BG = "#2a2a2a"


class TableListPanel(ctk.CTkFrame):
    """پنل لیست جداول با گروه"""

    def __init__(self, master, on_select=None, on_add=None,
                 on_reset=None, on_group_change=None):
        super().__init__(master, fg_color=BG_PANEL, corner_radius=8)
        self.on_select = on_select
        self.on_add = on_add
        self.on_reset = on_reset
        self.on_group_change = on_group_change   # ⭐

        self.current_table_id: int | None = None
        self._row_widgets: dict[int, ctk.CTkButton] = {}
        self._tables: list = []
        self._groups: list = []
        self._collapsed: set[int] = set()

        # ─── هدر ───
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkLabel(
            header, text="🗄️ جداول",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        self.count_lbl = ctk.CTkLabel(
            header, text="(0)", text_color="#888",
            font=ctk.CTkFont(size=11),
        )
        self.count_lbl.pack(side="left", padx=(6, 0))

        # ─── جستجو ───
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._apply_filter())

        ctk.CTkEntry(
            self,
            placeholder_text="🔍 جستجو...",
            textvariable=self.search_var,
            height=30, font=ctk.CTkFont(size=11),
        ).pack(fill="x", padx=10, pady=(4, 4))

        # ─── فیلتر گروه ───
        self.group_filter_var = ctk.StringVar(value="همه")
        self.group_filter = ctk.CTkOptionMenu(
            self,
            values=["همه"],
            variable=self.group_filter_var,
            height=28, font=ctk.CTkFont(size=11),
            command=lambda v: self._on_filter_change(v),
        )
        self.group_filter.pack(fill="x", padx=10, pady=(0, 6))

        # ─── لیست ───
        self.listbox = ctk.CTkScrollableFrame(self, fg_color=BG_LIST)
        self.listbox.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        # ─── دکمه‌های پایین ───
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=8, pady=(0, 8))

        ctk.CTkButton(
            bottom, text="➕  جدول جدید",
            fg_color="#0d6efd", hover_color="#0b5ed7",
            height=34, font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_add_click,
        ).pack(fill="x", pady=(0, 4))

        ctk.CTkButton(
            bottom, text="🔄  ریست به پیش‌فرض",
            fg_color="#6c1f1f", hover_color="#8a2828",
            height=30, font=ctk.CTkFont(size=11),
            command=self._on_reset_click,
        ).pack(fill="x")

    # ═════════════════════════════════════════════
    def load(self, groups: list, tables: list, current_group: str = "همه"):
        """بارگذاری گروه‌ها + جداول"""
        self._groups = groups
        self._tables = tables

        group_names = ["همه"] + [g.fa_name or g.name for g in groups]
        self.group_filter.configure(values=group_names)

        if current_group not in group_names:
            current_group = "همه"
        self.group_filter_var.set(current_group)

        self._render()

    # ═════════════════════════════════════════════
    def _render(self):
        for w in self.listbox.winfo_children():
            w.destroy()
        self._row_widgets.clear()

        filtered = self._filter_tables()

        if not filtered:
            ctk.CTkLabel(
                self.listbox,
                text="\n\n🔍 چیزی پیدا نشد",
                text_color="#666", font=ctk.CTkFont(size=12),
            ).pack(pady=20)
            self.count_lbl.configure(text="(0)")
            return

        current_filter = self.group_filter_var.get()
        if current_filter == "همه":
            # درخت‌واره
            for g in self._groups:
                group_tables = [t for t in filtered if t.group_id == g.id]
                if not group_tables:
                    continue
                self._render_group(g, group_tables)

            orphans = [t for t in filtered if t.group_id is None]
            if orphans:
                self._render_ungrouped(orphans)
        else:
            # لیست تخت
            for t in filtered:
                self._add_row(t)

        self.count_lbl.configure(text=f"({len(filtered)})")

    def _render_group(self, group, tables: list):
        is_collapsed = group.id in self._collapsed

        hdr = ctk.CTkButton(
            self.listbox,
            text=f"{'▶' if is_collapsed else '▼'} {group.icon}  "
                 f"{group.fa_name or group.name}  ({len(tables)})",
            anchor="w", height=32,
            fg_color=GROUP_HDR_BG, hover_color="#353535",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=group.color,
            command=lambda gid=group.id: self._toggle_group(gid),
        )
        hdr.pack(fill="x", pady=(4, 1), padx=2)

        if not is_collapsed:
            for t in tables:
                self._add_row(t, indent=True)

    def _render_ungrouped(self, tables: list):
        ctk.CTkLabel(
            self.listbox,
            text=f"📂  بدون گروه  ({len(tables)})",
            anchor="w", height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#888",
        ).pack(fill="x", pady=(4, 1), padx=4)

        for t in tables:
            self._add_row(t, indent=True)

    def _toggle_group(self, group_id: int):
        if group_id in self._collapsed:
            self._collapsed.remove(group_id)
        else:
            self._collapsed.add(group_id)
        self._render()

    def _add_row(self, table, indent: bool = False):
        icon = "🔒" if table.is_default else "📋"
        pad = "    " if indent else ""
        text = (f"{pad}{icon}  {table.name}\n"
                f"{pad}     {table.fa_name}  ({len(table.columns)} فیلد)")

        btn = ctk.CTkButton(
            self.listbox,
            text=text,
            anchor="w", height=46,
            fg_color=ROW_DEFAULT if table.is_default and table.id != self.current_table_id else ROW_BG,
            hover_color=ROW_HOV,
            font=ctk.CTkFont(size=10),
            command=lambda tid=table.id: self._on_click(tid),
        )
        btn.pack(fill="x", pady=2, padx=2)
        self._row_widgets[table.id] = btn

    def _on_click(self, table_id: int):
        self.current_table_id = table_id
        for tid, btn in self._row_widgets.items():
            table = next((t for t in self._tables if t.id == tid), None)
            if not table:
                continue
            if tid == table_id:
                btn.configure(fg_color=ROW_SEL, hover_color="#0b5ed7")
            elif table.is_default:
                btn.configure(fg_color=ROW_DEFAULT, hover_color=ROW_HOV)
            else:
                btn.configure(fg_color=ROW_BG, hover_color=ROW_HOV)

        if self.on_select:
            self.on_select(table_id)

    def _on_add_click(self):
        if self.on_add:
            self.on_add()

    def _on_reset_click(self):
        if self.on_reset:
            self.on_reset()

    def _on_filter_change(self, value: str):
        if self.on_group_change:
            self.on_group_change(value)
        self._render()

    # ═════════════════════════════════════════════
    def _filter_tables(self) -> list:
        q = self.search_var.get().strip().lower()
        current_group = self.group_filter_var.get()
        result = self._tables

        if current_group != "همه":
            group = next(
                (g for g in self._groups
                 if (g.fa_name or g.name) == current_group),
                None,
            )
            if group:
                result = [t for t in result if t.group_id == group.id]

        if q:
            result = [
                t for t in result
                if q in t.name.lower()
                or q in (t.fa_name or "").lower()
                or q in (t.description or "").lower()
                or any(q in c.name.lower() or q in (c.fa_name or "").lower()
                       for c in t.columns)
            ]

        return result

    def _apply_filter(self):
        self._render()

    def select_table(self, table_id: int):
        self._on_click(table_id)