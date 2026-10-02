# src/views/schema_designer/sections/columns_editor.py
"""
ColumnsEditor — ویرایش فیلدهای جدول
─────────────────────────────────
• هر ستون عرض اختصاصی داره
• padx هر ستون هم اختصاصی
• هدر و ردیف‌ها دقیقاً هم‌تراز
• dropdown گروه بالای جدول
"""

import customtkinter as ctk
from tkinter import messagebox

from src.models.custom_schema import (
    CustomTable, CustomColumn, DATA_TYPES, validate_name,
)


# ─── رنگ‌بندی ───
BG_PANEL = "#232323"
BG_LIST  = "#1a1a1a"
ROW_BG   = "#2e2e2e"
ROW_BG2  = "#262626"

EN_BORDER = "#0d6efd"
FA_BORDER = "#198754"
EN_BG     = "#16263f"
FA_BG     = "#163a26"


# ═══════════════════════════════════════════════════════════
# تعریف ستون‌ها: (key, header_text, width, padx, color)
# ═══════════════════════════════════════════════════════════
COLUMNS = [
    ("name",       "🇬🇧 EN",    130, 10,  EN_BORDER),
    ("fa_name",    "🇮🇷 FA",    120, 12,  FA_BORDER),
    ("data_type",  "نوع داده",   140, 12,  "#9ecbff"),
    ("allow_null", "NULL?",      55, 10,  "#9ecbff"),
    ("default",    "پیش‌فرض",    150, 8,   "#9ecbff"),
    ("pk",         "PK",         90, 0,   "#9ecbff"),
    ("unique",     "Unique",     90, 0,   "#9ecbff"),
    ("auto",       "Auto",       90, 0,   "#9ecbff"),
    ("search",     "جستجو",      90, 0,   "#9ecbff"),
    ("delete",     "",           90, 0,   "#9ecbff"),
]

# ─── نام‌های کلیدی برای دسترسی سریع ───
COL_INDEX = {c[0]: i for i, c in enumerate(COLUMNS)}
COL_WIDTH = {c[0]: c[2] for c in COLUMNS}
COL_PADX  = {c[0]: c[3] for c in COLUMNS}


class ColumnsEditor(ctk.CTkFrame):
    """ویرایشگر فیلدها"""

    def __init__(self, master, on_save=None):
        super().__init__(master, fg_color=BG_PANEL, corner_radius=8)
        self.on_save = on_save
        self.table: CustomTable | None = None
        self._field_vars: list[dict] = []
        self._groups: list = []   # ⭐ لیست گروه‌ها

        # ─── هدر ───
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 4))

        self.title_lbl = ctk.CTkLabel(
            header,
            text="📋 یک جدول انتخاب کنید",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.title_lbl.pack(side="left")

        self.info_lbl = ctk.CTkLabel(
            header, text="",
            text_color="#888", font=ctk.CTkFont(size=11),
        )
        self.info_lbl.pack(side="right")

        # ─── اطلاعات جدول ───
        self._build_table_info()

        # ─── هدر ستون‌ها ───
        self._build_columns_header()

        # ─── لیست فیلدها ───
        self.fields_frame = ctk.CTkScrollableFrame(self, fg_color=BG_LIST)
        self.fields_frame.pack(fill="both", expand=True, padx=10, pady=(2, 6))

        # ─── دکمه‌ها ───
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(
            bottom, text="➕  افزودن فیلد",
            fg_color="#0d6efd", hover_color="#0b5ed7",
            width=140, height=34,
            font=ctk.CTkFont(size=12),
            command=self._add_field,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            bottom, text="💾  ذخیره جدول",
            fg_color="#198754", hover_color="#146c43",
            width=140, height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._save,
        ).pack(side="right")

        self.empty_lbl = ctk.CTkLabel(
            self.fields_frame,
            text="\n\n👈  یک جدول انتخاب کنید",
            text_color="#666", font=ctk.CTkFont(size=12),
        )
        self.empty_lbl.pack(pady=20)

    # ═════════════════════════════════════════════
    def _setup_grid(self, frame):
        """تنظیم عرض ستون‌های grid بر اساس COLUMNS"""
        for i, (key, _, width, _, _) in enumerate(COLUMNS):
            frame.grid_columnconfigure(i, minsize=width, weight=0)

    # ═════════════════════════════════════════════
    # اطلاعات جدول + dropdown گروه
    # ═════════════════════════════════════════════
    def _build_table_info(self):
        info_frame = ctk.CTkFrame(self, fg_color="#1c1c1c", corner_radius=6)
        info_frame.pack(fill="x", padx=10, pady=(4, 8))

        # ─── ردیف گروه ───
        group_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        group_row.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkLabel(
            group_row, text="📁 گروه:",
            width=100, anchor="w",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#9ecbff",
        ).pack(side="left")

        self.group_var = ctk.StringVar(value="—")
        self.group_menu = ctk.CTkOptionMenu(
            group_row,
            values=["—"],
            variable=self.group_var,
            width=220, height=30,
            font=ctk.CTkFont(size=11),
        )
        self.group_menu.pack(side="left")

        # ─── ردیف نام ───
        name_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        name_row.pack(fill="x", padx=10, pady=(4, 6))

        ctk.CTkLabel(
            name_row, text="🇬🇧 نام (EN):",
            width=100, anchor="w",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=EN_BORDER,
        ).pack(side="left")

        self.name_var = ctk.StringVar()
        ctk.CTkEntry(
            name_row, textvariable=self.name_var,
            width=180, height=30,
            border_color=EN_BORDER, border_width=2,
            placeholder_text="English only", fg_color=EN_BG,
        ).pack(side="left", padx=(0, 16))

        ctk.CTkLabel(
            name_row, text="🇮🇷 نام (FA):",
            width=100, anchor="w",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=FA_BORDER,
        ).pack(side="left")

        self.fa_var = ctk.StringVar()
        ctk.CTkEntry(
            name_row, textvariable=self.fa_var,
            width=180, height=30,
            border_color=FA_BORDER, border_width=2,
            placeholder_text="فارسی", fg_color=FA_BG,
        ).pack(side="left")

        # ─── ردیف توضیحات ───
        desc_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        desc_row.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(
            desc_row, text="توضیحات:",
            width=100, anchor="w",
            font=ctk.CTkFont(size=11),
        ).pack(side="left")

        self.desc_var = ctk.StringVar()
        ctk.CTkEntry(desc_row, textvariable=self.desc_var, height=28).pack(
            side="left", fill="x", expand=True
        )

    # ═════════════════════════════════════════════
    # هدر ستون‌ها
    # ═════════════════════════════════════════════
    def _build_columns_header(self):
        header = ctk.CTkFrame(self, fg_color="#2a2a2a", corner_radius=4)
        header.pack(fill="x", padx=20, pady=(4, 2))

        self._setup_grid(header)

        for i, (key, text, width, padx, color) in enumerate(COLUMNS):
            ctk.CTkLabel(
                header, text=text,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=color,
                anchor="center",
            ).grid(row=0, column=i, padx=padx*(width/25)+i, pady=18, sticky="ew")

    # ═════════════════════════════════════════════
    # API گروه‌ها
    # ═════════════════════════════════════════════
    def set_groups(self, groups: list):
        """تنظیم لیست گروه‌ها برای dropdown"""
        self._groups = groups
        values = ["—"] + [g.fa_name or g.name for g in groups]
        self.group_menu.configure(values=values)

    def _select_current_group(self):
        """انتخاب گروه فعلی جدول توی dropdown"""
        if not self.table:
            self.group_var.set("—")
            return

        if self.table.group_id is None:
            self.group_var.set("—")
            return

        g = next((g for g in self._groups if g.id == self.table.group_id), None)
        if g:
            self.group_var.set(g.fa_name or g.name)
        else:
            self.group_var.set("—")

    def _resolve_group_id(self) -> int | None:
        """تبدیل نام گروه به id"""
        group_name = self.group_var.get()
        if group_name == "—":
            return None
        g = next((g for g in self._groups
                  if (g.fa_name or g.name) == group_name), None)
        return g.id if g else None

    # ═════════════════════════════════════════════
    # بارگذاری جدول
    # ═════════════════════════════════════════════
    def load_table(self, table: CustomTable):
        self.table = table
        self.title_lbl.configure(text=f"📋 {table.name}")
        self.info_lbl.configure(
            text=f"{'🔒 پیش‌فرض' if table.is_default else '📋 سفارشی'}  •  "
                 f"{len(table.columns)} فیلد"
        )

        self.name_var.set(table.name)
        self.fa_var.set(table.fa_name)
        self.desc_var.set(table.description)

        self._select_current_group()   # ⭐

        self._render_fields()

    def _render_fields(self):
        for w in self.fields_frame.winfo_children():
            w.destroy()
        self._field_vars.clear()

        if not self.table or not self.table.columns:
            ctk.CTkLabel(
                self.fields_frame,
                text="\n\nهیچ فیلدی وجود ندارد",
                text_color="#666", font=ctk.CTkFont(size=12),
            ).pack(pady=20)
            return

        for i, col in enumerate(self.table.columns):
            self._add_field_row(i, col)

    # ═════════════════════════════════════════════
    # ردیف فیلد
    # ═════════════════════════════════════════════
    def _add_field_row(self, index: int, col: CustomColumn):
        bg = ROW_BG if index % 2 == 0 else ROW_BG2
        row = ctk.CTkFrame(self.fields_frame, fg_color=bg, corner_radius=4)
        row.pack(fill="x", pady=1)

        self._setup_grid(row)

        # ─── متغیرها ───
        name_var    = ctk.StringVar(value=col.name)
        fa_var      = ctk.StringVar(value=col.fa_name)
        type_var    = ctk.StringVar(value=col.data_type)
        null_var    = ctk.BooleanVar(value=col.allow_null)
        default_var = ctk.StringVar(value=col.default_value)
        pk_var      = ctk.BooleanVar(value=col.is_primary)
        unique_var  = ctk.BooleanVar(value=col.is_unique)
        auto_var    = ctk.BooleanVar(value=col.is_auto_increment)
        search_var  = ctk.BooleanVar(value=col.is_searchable)

        # ═══ col 0: EN ═══
        ctk.CTkEntry(
            row, textvariable=name_var, height=28,
            border_color=EN_BORDER, border_width=2,
            placeholder_text="english_name", fg_color=EN_BG,
        ).grid(
            row=0, column=COL_INDEX["name"],
            padx=COL_PADX["name"], pady=4, sticky="ew",
        )

        # ═══ col 1: FA ═══
        ctk.CTkEntry(
            row, textvariable=fa_var, height=28,
            border_color=FA_BORDER, border_width=2,
            placeholder_text="نام فارسی", fg_color=FA_BG,
        ).grid(
            row=0, column=COL_INDEX["fa_name"],
            padx=COL_PADX["fa_name"], pady=4, sticky="ew",
        )

        # ═══ col 2: نوع داده ═══
        ctk.CTkOptionMenu(
            row, values=DATA_TYPES, variable=type_var,
            height=28, font=ctk.CTkFont(size=10),
        ).grid(
            row=0, column=COL_INDEX["data_type"],
            padx=COL_PADX["data_type"], pady=4, sticky="ew",
        )

        # ═══ col 3: NULL ═══
        ctk.CTkCheckBox(
            row, text="", variable=null_var,
            width=24, checkbox_width=20, checkbox_height=20,
        ).grid(
            row=0, column=COL_INDEX["allow_null"],
            padx=COL_PADX["allow_null"], pady=4,
        )

        # ═══ col 4: پیش‌فرض ═══
        ctk.CTkEntry(
            row, textvariable=default_var, height=28,
            placeholder_text="NULL / CURRENT",
        ).grid(
            row=0, column=COL_INDEX["default"],
            padx=COL_PADX["default"], pady=4, sticky="ew",
        )

        # ═══ col 5: PK ═══
        ctk.CTkCheckBox(
            row, text="", variable=pk_var,
            width=24, checkbox_width=18, checkbox_height=18,
        ).grid(
            row=0, column=COL_INDEX["pk"],
            padx=COL_PADX["pk"], pady=4,
        )

        # ═══ col 6: UNIQUE ═══
        ctk.CTkCheckBox(
            row, text="", variable=unique_var,
            width=24, checkbox_width=18, checkbox_height=18,
        ).grid(
            row=0, column=COL_INDEX["unique"],
            padx=COL_PADX["unique"], pady=4,
        )

        # ═══ col 7: AUTO ═══
        ctk.CTkCheckBox(
            row, text="", variable=auto_var,
            width=24, checkbox_width=18, checkbox_height=18,
        ).grid(
            row=0, column=COL_INDEX["auto"],
            padx=COL_PADX["auto"], pady=4,
        )

        # ═══ col 8: جستجو ═══
        ctk.CTkCheckBox(
            row, text="", variable=search_var,
            width=24, checkbox_width=18, checkbox_height=18,
        ).grid(
            row=0, column=COL_INDEX["search"],
            padx=COL_PADX["search"], pady=4,
        )

        # ═══ col 9: حذف ═══
        def delete_field(idx=index, c=col):
            if c.is_primary:
                messagebox.showwarning(
                    "خطا", "فیلد کلید اصلی رو نمی‌شه حذف کرد", parent=self,
                )
                return
            if not messagebox.askyesno(
                "حذف", f"فیلد «{c.name}» حذف بشه؟", parent=self,
            ):
                return
            self.table.columns.pop(idx)
            self._render_fields()

        ctk.CTkButton(
            row, text="🗑", width=36, height=28,
            fg_color="#6c1f1f", hover_color="#8a2828",
            font=ctk.CTkFont(size=11),
            command=delete_field,
        ).grid(
            row=0, column=COL_INDEX["delete"],
            padx=COL_PADX["delete"], pady=4,
        )

        self._field_vars.append({
            "name": name_var, "fa_name": fa_var,
            "data_type": type_var, "allow_null": null_var,
            "default_value": default_var, "is_primary": pk_var,
            "is_unique": unique_var, "is_auto_increment": auto_var,
            "is_searchable": search_var, "orig": col,
        })

    # ═════════════════════════════════════════════
    def _add_field(self):
        if not self.table:
            messagebox.showwarning("خطا", "ابتدا یک جدول انتخاب کنید", parent=self)
            return

        existing_names = {c.name for c in self.table.columns}
        n = 1
        while f"field_{n}" in existing_names:
            n += 1

        self.table.columns.append(CustomColumn(
            name=f"field_{n}", fa_name=f"فیلد {n}",
            data_type="VARCHAR(150)",
            allow_null=True, default_value="NULL",
            is_searchable=True,
        ))
        self._render_fields()

    # ═════════════════════════════════════════════
    def _save(self):
        if not self.table:
            return

        new_name = self.name_var.get().strip()
        ok, msg = validate_name(new_name)
        if not ok:
            messagebox.showwarning("نام جدول نامعتبر", msg, parent=self)
            return

        names_seen = set()
        for i, fv in enumerate(self._field_vars):
            name = fv["name"].get().strip()
            ok, msg = validate_name(name)
            if not ok:
                messagebox.showwarning(
                    f"فیلد {i+1} نامعتبر", f"نام '{name}': {msg}", parent=self,
                )
                return
            if name in names_seen:
                messagebox.showwarning(
                    "نام تکراری", f"نام '{name}' تکراریه", parent=self,
                )
                return
            names_seen.add(name)

        self.table.name = new_name
        self.table.fa_name = self.fa_var.get().strip()
        self.table.description = self.desc_var.get().strip()

        # ⭐ گروه
        self.table.group_id = self._resolve_group_id()

        for i, fv in enumerate(self._field_vars):
            col = fv["orig"]
            col.name = fv["name"].get().strip()
            col.fa_name = fv["fa_name"].get().strip()
            col.data_type = fv["data_type"].get()
            col.allow_null = fv["allow_null"].get()
            col.default_value = fv["default_value"].get().strip()
            col.is_primary = fv["is_primary"].get()
            col.is_unique = fv["is_unique"].get()
            col.is_auto_increment = fv["is_auto_increment"].get()
            col.is_searchable = fv["is_searchable"].get()
            col.order_index = i

        if self.on_save:
            self.on_save(self.table)