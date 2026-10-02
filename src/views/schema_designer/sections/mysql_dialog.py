# src/views/schema_designer/sections/mysql_dialog.py
"""
MySQLDialog — دیالوگ اتصال و ساخت جداول در MySQL
"""

import customtkinter as ctk
from tkinter import messagebox

from src.services.db_connector import DBConnector
from src.services.mysql_generator import MySQLGenerator


BG_DIALOG = "#1e1e1e"


class MySQLDialog(ctk.CTkToplevel):
    """دیالوگ ساخت جداول در MySQL"""

    def __init__(self, master, tables: list, project):
        super().__init__(master)
        self.tables = tables
        self.project = project
        self.connector: DBConnector | None = None

        self.title("⚡ ساخت جداول در MySQL")
        self.geometry("640x760")
        self.minsize(560, 640)
        self.configure(fg_color=BG_DIALOG)

        self.transient(master)
        self.grab_set()

        # ⭐ نام دیتابیس پیش‌فرض: {project.name}_db
        default_db = f"{self.project.name}_db" if self.project else "py_app_db"

        # ═══ مقادیر ═══
        self._host_var = ctk.StringVar(value="localhost")
        self._port_var = ctk.StringVar(value="3306")
        self._user_var = ctk.StringVar(value="root")
        self._pass_var = ctk.StringVar(value="")
        self._db_var = ctk.StringVar(value=default_db)
        self._drop_var = ctk.BooleanVar(value=False)

        # ═══ UI ═══
        self._build()

        self.bind("<Escape>", lambda e: self._close())
        self.after(50, self.focus_force)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build(self):
        # ═══ هدر ═══
        header = ctk.CTkFrame(self, fg_color="#252525", height=60, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="⚡  ساخت جداول در MySQL",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left", padx=16)

        project_name = (
            self.project.fa_name or self.project.name
            if self.project else "—"
        )
        ctk.CTkLabel(
            header,
            text=f"📦 {project_name}",
            text_color="#fd7e14",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="right", padx=16)

        # ═══ بدنه ═══
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=14, pady=12)

        # ─── اتصال ───
        self._section(body, "🔌 اتصال MySQL")

        self._field(body, "Host:", self._host_var)
        self._field(body, "Port:", self._port_var)
        self._field(body, "User:", self._user_var)
        self._field(body, "Password:", self._pass_var, show="*")

        # ─── دیتابیس ───
        self._section(body, "🗄️ دیتابیس")

        db_row = ctk.CTkFrame(body, fg_color="#2e2e2e", corner_radius=6)
        db_row.pack(fill="x", pady=3)

        ctk.CTkLabel(
            db_row, text="نام دیتابیس:",
            width=140, anchor="w",
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(10, 6), pady=8)

        ctk.CTkEntry(
            db_row, textvariable=self._db_var,
            height=30,
        ).pack(side="left", fill="x", expand=True, padx=(0, 10), pady=8)

        ctk.CTkLabel(
            body,
            text=f"💡 collation: utf8mb4_persian_ci  •  charset: utf8mb4",
            text_color="#9ecbff", font=ctk.CTkFont(size=10), anchor="w",
        ).pack(fill="x", padx=8, pady=(0, 2))

        ctk.CTkLabel(
            body,
            text="⚠️ اگه دیتابیس وجود نداشته باشه، ساخته می‌شه",
            text_color="#888", font=ctk.CTkFont(size=10), anchor="w",
        ).pack(fill="x", padx=8, pady=(0, 4))

        # ─── دکمه تست ───
        test_row = ctk.CTkFrame(body, fg_color="transparent")
        test_row.pack(fill="x", pady=(4, 8))

        ctk.CTkButton(
            test_row, text="🔍  تست اتصال",
            width=140, height=34,
            fg_color="#0d6efd", hover_color="#0b5ed7",
            font=ctk.CTkFont(size=12),
            command=self._test_connection,
        ).pack(side="left")

        self.status_lbl = ctk.CTkLabel(
            test_row, text="",
            font=ctk.CTkFont(size=11),
            anchor="w",
        )
        self.status_lbl.pack(side="left", padx=10)

        # ─── آمار جداول ───
        self._section(body, "📊 جداولی که ساخته می‌شن")

        stats_frame = ctk.CTkFrame(body, fg_color="#1c1c1c", corner_radius=6)
        stats_frame.pack(fill="x", pady=4)

        total_cols = sum(len(t.columns) for t in self.tables)
        ctk.CTkLabel(
            stats_frame,
            text=f"📋 {len(self.tables)} جدول  •  📊 {total_cols} ستون",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9ecbff",
        ).pack(pady=8, padx=10)

        for t in sorted(self.tables, key=lambda x: (not x.is_default, x.order_index)):
            icon = "🔒" if t.is_default else "📋"
            ctk.CTkLabel(
                stats_frame,
                text=f"  {icon}  {t.name}  ({len(t.columns)} ستون)",
                anchor="w",
                font=ctk.CTkFont(size=11),
            ).pack(fill="x", padx=12, pady=1)

        ctk.CTkLabel(stats_frame, text="").pack(pady=2)

        # ─── گزینه‌ها ───
        self._section(body, "⚙️ گزینه‌ها")

        drop_row = ctk.CTkFrame(body, fg_color="#2e2e2e", corner_radius=6)
        drop_row.pack(fill="x", pady=3)

        ctk.CTkCheckBox(
            drop_row,
            text="جداول موجود رو DROP کن (⚠️ خطرناک)",
            variable=self._drop_var,
            font=ctk.CTkFont(size=12),
            text_color="#ff8888",
        ).pack(side="left", padx=12, pady=10)

        # ─── دکمه پیش‌نمایش ───
        ctk.CTkButton(
            body, text="👁  پیش‌نمایش SQL",
            width=200, height=36,
            fg_color="#6f42c1", hover_color="#5a32a3",
            font=ctk.CTkFont(size=12),
            command=self._preview_sql,
        ).pack(pady=(12, 4))

        # ═══ نوار پایین ═══
        footer = ctk.CTkFrame(self, fg_color="#252525", height=64, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        ctk.CTkButton(
            footer, text="⚡  ساخت جداول",
            width=180, height=40,
            fg_color="#198754", hover_color="#146c43",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._create_tables,
        ).pack(side="right", padx=(6, 14), pady=12)

        ctk.CTkButton(
            footer, text="انصراف",
            width=100, height=40,
            fg_color="#444", hover_color="#555",
            command=self._close,
        ).pack(side="right", padx=6, pady=12)

    def _section(self, parent, title: str):
        ctk.CTkLabel(
            parent, text=title,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9ecbff", anchor="w",
        ).pack(fill="x", pady=(12, 4), padx=2)

    def _field(self, parent, label: str, var, show: str = ""):
        row = ctk.CTkFrame(parent, fg_color="#2e2e2e", corner_radius=6)
        row.pack(fill="x", pady=3)

        ctk.CTkLabel(
            row, text=label, width=140, anchor="w",
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(10, 6), pady=8)

        entry = ctk.CTkEntry(row, textvariable=var, height=30, show=show)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=8)

    # ═════════════════════════════════════════════
    def _test_connection(self):
        try:
            host = self._host_var.get().strip()
            port = int(self._port_var.get().strip() or "3306")
            user = self._user_var.get().strip()
            password = self._pass_var.get()

            self.status_lbl.configure(text="⏳ در حال تست...", text_color="#ffc107")
            self.update()

            ok, msg = DBConnector.test_connection(host, port, user, password)

            if ok:
                self.status_lbl.configure(text=msg, text_color="#7bd88f")
            else:
                self.status_lbl.configure(text=msg, text_color="#ff6b6b")

        except Exception as e:
            self.status_lbl.configure(text=f"❌ {e}", text_color="#ff6b6b")

    def _preview_sql(self):
        sql = MySQLGenerator.generate_all(
            self.tables,
            with_drop=self._drop_var.get(),
        )
        preview = _SQLPreview(self, sql)
        self.wait_window(preview)

    def _create_tables(self):
        db_name = self._db_var.get().strip()
        if not db_name:
            messagebox.showwarning("خطا", "نام دیتابیس رو وارد کنید", parent=self)
            return

        try:
            port = int(self._port_var.get().strip() or "3306")
        except ValueError:
            messagebox.showwarning("خطا", "Port باید عدد باشه", parent=self)
            return

        drop_warning = ""
        if self._drop_var.get():
            drop_warning = "\n\n⚠️ جداول موجود DROP می‌شن!"

        if not messagebox.askyesno(
            "تأیید",
            f"جداول در دیتابیس «{db_name}» ساخته بشن؟\n\n"
            f"📋 {len(self.tables)} جدول{drop_warning}",
            parent=self,
        ):
            return

        # ─── اتصال ───
        self.status_lbl.configure(text="⏳ اتصال...", text_color="#ffc107")
        self.update()

        connector = DBConnector(
            host=self._host_var.get().strip(),
            port=port,
            user=self._user_var.get().strip(),
            password=self._pass_var.get(),
            database=db_name,
        )

        ok, msg = connector.connect(create_db_if_missing=True)
        if not ok:
            messagebox.showerror("خطا در اتصال", msg, parent=self)
            self.status_lbl.configure(text=msg, text_color="#ff6b6b")
            return

        # ─── تولید SQL ───
        sql = MySQLGenerator.generate_all(
            self.tables,
            with_drop=self._drop_var.get(),
            add_header=False,
        )

        # ─── اجرا ───
        self.status_lbl.configure(text="⏳ در حال اجرا...", text_color="#ffc107")
        self.update()

        ok, msg = connector.execute_sql(sql)
        connector.disconnect()

        if ok:
            self.status_lbl.configure(text=msg, text_color="#7bd88f")
            messagebox.showinfo(
                "موفق",
                f"{msg}\n\n"
                f"📊 دیتابیس: {db_name}\n"
                f"📋 {len(self.tables)} جدول",
                parent=self,
            )
            self._close()
        else:
            self.status_lbl.configure(text=msg, text_color="#ff6b6b")
            messagebox.showerror("خطای اجرا", msg, parent=self)

    def _close(self):
        if self.connector:
            self.connector.disconnect()
        self.destroy()


# ═══════════════════════════════════════════════════════════
class _SQLPreview(ctk.CTkToplevel):
    def __init__(self, master, sql: str):
        super().__init__(master)
        self.title("👁 پیش‌نمایش SQL")
        self.geometry("900x700")
        self.configure(fg_color="#1a1a1a")

        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(
            self, text="👁  پیش‌نمایش SQL",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(16, 8))

        textbox = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="none",
        )
        textbox.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        textbox.insert("1.0", sql)
        textbox.configure(state="disabled")

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=14, pady=(0, 14))

        ctk.CTkButton(
            btns, text="📋  کپی در کلیپ‌بورد",
            width=180, height=36,
            fg_color="#0d6efd", hover_color="#0b5ed7",
            command=lambda: self._copy(sql),
        ).pack(side="left")

        ctk.CTkButton(
            btns, text="بستن",
            width=100, height=36,
            fg_color="#444", hover_color="#555",
            command=self.destroy,
        ).pack(side="right")

        self.bind("<Escape>", lambda e: self.destroy())
        self.after(50, self.focus_force)

    def _copy(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("کپی شد", "SQL توی کلیپ‌بورد کپی شد", parent=self)