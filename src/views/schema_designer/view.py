# src/views/schema_designer/view.py
"""
Schema Designer — طراحی جداول
─────────────────────────────────
• پروژه‌ی فعال
• نمایش نام پروژه توی هدر
• دکمه‌ی ساخت جداول در MySQL
"""

import customtkinter as ctk
from tkinter import messagebox

from src.services.schema_store import SchemaStore
from src.services.schema_seeder import SchemaSeeder
from src.models.custom_schema import CustomTable, TableGroup

from .sections import TableListPanel, ColumnsEditor, MySQLDialog


BG_WINDOW = "#1a1a1a"


class SchemaDesignerView(ctk.CTkToplevel):
    """Schema Designer"""

    def __init__(self, master=None, on_close=None):
        super().__init__(master)
        self.on_close = on_close

        # ═══ State ═══
        self.store = SchemaStore()
        self.seeder = SchemaSeeder(self.store)
        self.project = self.store.get_active_project()
        self.current_table: CustomTable | None = None
        self.groups: list = []

        # ═══ Seed ═══
        self.seeder.seed_if_empty(self.project.id)

        # ═══ تنظیمات پنجره ═══
        name = self.project.fa_name or self.project.name
        self.title(f"🗄️ Schema Designer — {name}")
        self.geometry("1500x820")
        self.minsize(1200, 650)
        self.configure(fg_color=BG_WINDOW)

        # ═══ Layout ═══
        self._build_layout()
        self._load_all()

        self.after(50, self.focus_force)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ═════════════════════════════════════════════
    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0, minsize=280)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ═══ سایدبار چپ ═══
        self.table_panel = TableListPanel(
            self,
            on_select=self._on_table_select,
            on_add=self._on_add_table,
            on_reset=self._on_reset_tables,
            on_group_change=self._on_group_filter_change,
        )
        self.table_panel.grid(row=0, column=0, sticky="nsew",
                              padx=(10, 5), pady=(10, 5))

        # ═══ ویرایشگر راست ═══
        self.columns_editor = ColumnsEditor(
            self, on_save=self._on_save_table,
        )
        self.columns_editor.grid(row=0, column=1, sticky="nsew",
                                  padx=(5, 10), pady=(10, 5))

        # ═══ نوار پایین ═══
        self._build_bottom_bar()

    def _build_bottom_bar(self):
        bar = ctk.CTkFrame(self, fg_color="#181818", height=56, corner_radius=6)
        bar.grid(row=1, column=0, columnspan=2, sticky="ew",
                 padx=10, pady=(5, 10))
        bar.grid_propagate(False)

        # ─── 📦 نام پروژه ───
        self.project_lbl = ctk.CTkLabel(
            bar,
            text=f"📦 {self.project.fa_name or self.project.name}",
            text_color="#fd7e14",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.project_lbl.pack(side="left", padx=(14, 8), pady=10)

        # ─── جداکننده ───
        ctk.CTkFrame(
            bar, fg_color="#444", width=1, height=28, corner_radius=0,
        ).pack(side="left", padx=6, pady=14)

        # ─── 🏠 بستن ───
        ctk.CTkButton(
            bar, text="🏠  بستن", width=100,
            fg_color="#dc3545", hover_color="#b02a37",
            command=self._on_close,
        ).pack(side="left", padx=6, pady=10)

        # ─── 💾 ذخیره ───
        ctk.CTkButton(
            bar, text="💾  ذخیره", width=110,
            fg_color="#0d6efd", hover_color="#0b5ed7",
            command=self._save_all,
        ).pack(side="left", padx=6, pady=10)

        # ─── 🗑 حذف ───
        ctk.CTkButton(
            bar, text="🗑  حذف", width=100,
            fg_color="#6c1f1f", hover_color="#8a2828",
            command=self._on_delete_current,
        ).pack(side="left", padx=6, pady=10)

        # ─── 📁 گروه ───
        ctk.CTkButton(
            bar, text="📁  گروه جدید", width=130,
            fg_color="#6f42c1", hover_color="#5a32a3",
            command=self._add_group,
        ).pack(side="left", padx=6, pady=10)

        # ─── ⚡ MySQL (سمت راست، مهم‌ترین) ───
        ctk.CTkButton(
            bar, text="⚡  ساخت جداول در MySQL", width=220, height=38,
            fg_color="#198754", hover_color="#146c43",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._create_mysql,
        ).pack(side="right", padx=(6, 14), pady=9)

        self.status_lbl = ctk.CTkLabel(
            bar, text="آماده", text_color="#aaa",
            font=ctk.CTkFont(size=11),
        )
        self.status_lbl.pack(side="right", padx=14)

    # ═════════════════════════════════════════════
    def _load_all(self):
        self.groups = self.store.list_groups(self.project.id)
        tables = self.store.list_tables(self.project.id)

        last_group = self.store.get_setting(
            self.project.id, "last_group_filter", "همه",
        )

        self.table_panel.load(self.groups, tables, current_group=last_group)
        self.columns_editor.set_groups(self.groups)

        # ⭐ آپدیت نام پروژه توی نوار پایین
        if hasattr(self, "project_lbl"):
            name = self.project.fa_name or self.project.name
            self.project_lbl.configure(text=f"📦 {name}")

        self._set_status(
            f"{len(tables)} جدول • {len(self.groups)} گروه"
        )

    def _on_table_select(self, table_id: int):
        table = self.store.get_table(table_id)
        if table is None:
            return
        self.current_table = table
        self.columns_editor.load_table(table)

    def _on_group_filter_change(self, group_name: str):
        self.store.set_setting(
            self.project.id, "last_group_filter", group_name,
        )

    def _on_add_table(self):
        dialog = _NewTableDialog(self, self.groups)
        self.wait_window(dialog)

        if dialog.result:
            name, fa_name, group_id = dialog.result

            existing_names = {t.name for t in self.store.list_tables(self.project.id)}
            if name in existing_names:
                messagebox.showwarning(
                    "نام تکراری",
                    f"جدول «{name}» از قبل وجود داره",
                    parent=self,
                )
                return

            table = CustomTable.create_empty(
                project_id=self.project.id, name=name, fa_name=fa_name,
            )
            table.group_id = group_id

            tables = self.store.list_tables(self.project.id)
            table.order_index = max((t.order_index for t in tables), default=0) + 1

            self.store.save_table(table)
            self._load_all()
            self.table_panel.select_table(table.id)
            self._set_status(f"✅ جدول {name} ساخته شد")

    def _on_delete_current(self):
        if not self.current_table:
            messagebox.showwarning("خطا", "ابتدا یک جدول انتخاب کنید", parent=self)
            return

        if self.current_table.is_default:
            if not messagebox.askyesno(
                "حذف جدول پیش‌فرض",
                f"«{self.current_table.name}» پیش‌فرضه.\nمطمئنی؟",
                parent=self,
            ):
                return

        if not messagebox.askyesno(
            "حذف",
            f"جدول «{self.current_table.name}» حذف بشه؟",
            parent=self,
        ):
            return

        self.store.delete_table(self.current_table.id)
        self.current_table = None
        self.columns_editor.table = None
        self.columns_editor._render_fields()
        self.columns_editor.title_lbl.configure(text="📋 یک جدول انتخاب کنید")
        self._load_all()
        self._set_status("🗑 جدول حذف شد")

    def _on_reset_tables(self):
        if not messagebox.askyesno(
            "ریست به پیش‌فرض",
            "همه‌ی جداول و گروه‌های این پروژه پاک می‌شن.\n"
            "همه‌ی تغییرات از بین می‌ره!\n\nمطمئنی؟",
            parent=self,
        ):
            return

        result = self.seeder.reset_to_defaults(self.project.id)
        self.current_table = None
        self.columns_editor.table = None
        self.columns_editor._render_fields()
        self.columns_editor.title_lbl.configure(text="📋 یک جدول انتخاب کنید")
        self._load_all()
        self._set_status(
            f"🔄 {result['tables']} جدول و {result['groups']} گروه بارگذاری شد"
        )

    def _add_group(self):
        dialog = _NewGroupDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            name, fa_name, icon, color = dialog.result

            existing = {g.name for g in self.store.list_groups(self.project.id)}
            if name in existing:
                messagebox.showwarning(
                    "تکراری", f"گروه «{name}» از قبل هست", parent=self,
                )
                return

            groups = self.store.list_groups(self.project.id)
            g = TableGroup(
                project_id=self.project.id,
                name=name, fa_name=fa_name,
                icon=icon, color=color,
                order_index=max((x.order_index for x in groups), default=0) + 1,
            )
            self.store.save_group(g)
            self._load_all()
            self._set_status(f"✅ گروه {fa_name} ساخته شد")

    def _on_save_table(self, table: CustomTable):
        try:
            self.store.save_table(table)
            self._load_all()
            self.table_panel.select_table(table.id)
            self._set_status(f"💾 {table.name} ذخیره شد")
        except Exception as e:
            messagebox.showerror("خطای ذخیره", str(e), parent=self)

    def _save_all(self):
        if self.current_table:
            self._on_save_table(self.current_table)

    # ═════════════════════════════════════════════
    # ⭐ ساخت جداول در MySQL
    # ═════════════════════════════════════════════
    def _create_mysql(self):
        # اول ذخیره‌ی تغییرات فعلی
        if self.current_table:
            self._on_save_table(self.current_table)

        # بارگذاری مجدد
        tables = self.store.list_tables(self.project.id)

        if not tables:
            messagebox.showwarning(
                "بدون جدول",
                "هیچ جدولی توی این پروژه نیست.",
                parent=self,
            )
            return

        # باز کردن دیالوگ
        MySQLDialog(self, tables, self.project)

    # ═════════════════════════════════════════════
    def _on_close(self):
        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass
        self.destroy()

    def _set_status(self, text: str):
        self.status_lbl.configure(text=text)


# ═══════════════════════════════════════════════════════════
# دیالوگ جدول جدید (بدون تغییر)
# ═══════════════════════════════════════════════════════════
class _NewTableDialog(ctk.CTkToplevel):
    def __init__(self, master, groups: list):
        super().__init__(master)
        self.result: tuple[str, str, int | None] | None = None
        self._groups = groups

        self.title("جدول جدید")
        self.geometry("440x320")
        self.resizable(False, False)
        self.configure(fg_color="#1e1e1e")
        self.transient(master); self.grab_set()

        ctk.CTkLabel(self, text="➕  جدول جدید",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(pady=(20, 14))

        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(row1, text="🇬🇧 نام (EN):", width=100, anchor="w",
                     text_color="#0d6efd").pack(side="left")
        self.name_var = ctk.StringVar(value="new_table")
        ctk.CTkEntry(row1, textvariable=self.name_var, height=30).pack(
            side="left", fill="x", expand=True)

        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(row2, text="🇮🇷 نام (FA):", width=100, anchor="w",
                     text_color="#198754").pack(side="left")
        self.fa_var = ctk.StringVar(value="جدول جدید")
        ctk.CTkEntry(row2, textvariable=self.fa_var, height=30).pack(
            side="left", fill="x", expand=True)

        row3 = ctk.CTkFrame(self, fg_color="transparent")
        row3.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(row3, text="📁 گروه:", width=100, anchor="w",
                     text_color="#9ecbff").pack(side="left")
        group_names = ["—"] + [g.fa_name or g.name for g in groups]
        self.group_var = ctk.StringVar(
            value=group_names[-1] if len(group_names) > 1 else "—"
        )
        ctk.CTkOptionMenu(row3, values=group_names, variable=self.group_var,
                          height=30).pack(side="left", fill="x", expand=True)

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(14, 20))
        ctk.CTkButton(btns, text="ساخت", fg_color="#198754",
                      hover_color="#146c43", width=100, height=36,
                      command=self._ok).pack(side="right", padx=(6, 0))
        ctk.CTkButton(btns, text="انصراف", fg_color="#444",
                      hover_color="#555", width=100, height=36,
                      command=self.destroy).pack(side="right")

        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())
        self.after(50, self.focus_force)

    def _ok(self):
        name = self.name_var.get().strip()
        fa = self.fa_var.get().strip()
        from src.models.custom_schema import validate_name
        ok, msg = validate_name(name)
        if not ok:
            messagebox.showwarning("نام نامعتبر", msg, parent=self)
            return

        group_name = self.group_var.get()
        group_id = None
        if group_name != "—":
            g = next((g for g in self._groups
                      if (g.fa_name or g.name) == group_name), None)
            if g:
                group_id = g.id

        self.result = (name, fa, group_id)
        self.destroy()


# ═══════════════════════════════════════════════════════════
# دیالوگ گروه جدید (بدون تغییر)
# ═══════════════════════════════════════════════════════════
class _NewGroupDialog(ctk.CTkToplevel):
    ICONS = ["📁", "🔐", "📊", "📝", "🛒", "💰", "👥", "🎨", "⚙️", "🔧"]
    COLORS = ["#0d6efd", "#198754", "#fd7e14", "#6f42c1", "#dc3545",
              "#20c997", "#ffc107", "#e83e8c"]

    def __init__(self, master):
        super().__init__(master)
        self.result = None

        self.title("گروه جدید")
        self.geometry("420x360")
        self.resizable(False, False)
        self.configure(fg_color="#1e1e1e")
        self.transient(master); self.grab_set()

        ctk.CTkLabel(self, text="📁  گروه جدید",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(pady=(20, 14))

        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(row1, text="🇬🇧 نام (EN):", width=100, anchor="w",
                     text_color="#0d6efd").pack(side="left")
        self.name_var = ctk.StringVar(value="new_group")
        ctk.CTkEntry(row1, textvariable=self.name_var, height=30).pack(
            side="left", fill="x", expand=True)

        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(row2, text="🇮🇷 نام (FA):", width=100, anchor="w",
                     text_color="#198754").pack(side="left")
        self.fa_var = ctk.StringVar(value="گروه جدید")
        ctk.CTkEntry(row2, textvariable=self.fa_var, height=30).pack(
            side="left", fill="x", expand=True)

        row3 = ctk.CTkFrame(self, fg_color="transparent")
        row3.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(row3, text="آیکون:", width=100, anchor="w").pack(side="left")
        self.icon_var = ctk.StringVar(value="📁")
        ctk.CTkOptionMenu(row3, values=self.ICONS, variable=self.icon_var,
                          width=100, height=30).pack(side="left")

        row4 = ctk.CTkFrame(self, fg_color="transparent")
        row4.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(row4, text="رنگ:", width=100, anchor="w").pack(side="left")
        self.color_var = ctk.StringVar(value="#0d6efd")
        ctk.CTkOptionMenu(row4, values=self.COLORS, variable=self.color_var,
                          width=140, height=30).pack(side="left")

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(20, 20))
        ctk.CTkButton(btns, text="ساخت", fg_color="#198754",
                      hover_color="#146c43", width=100, height=36,
                      command=self._ok).pack(side="right", padx=(6, 0))
        ctk.CTkButton(btns, text="انصراف", fg_color="#444",
                      hover_color="#555", width=100, height=36,
                      command=self.destroy).pack(side="right")

        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())
        self.after(50, self.focus_force)

    def _ok(self):
        from src.models.custom_schema import validate_name
        name = self.name_var.get().strip()
        ok, msg = validate_name(name)
        if not ok:
            messagebox.showwarning("نام نامعتبر", msg, parent=self)
            return

        self.result = (
            name,
            self.fa_var.get().strip(),
            self.icon_var.get(),
            self.color_var.get(),
        )
        self.destroy()