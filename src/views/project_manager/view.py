# src/views/project_manager/view.py
"""
ProjectManagerView — مدیریت پروژه‌ها
"""

import customtkinter as ctk
from tkinter import messagebox

from src.services.schema_store import SchemaStore
from src.services.schema_seeder import SchemaSeeder
from src.models.custom_schema import Project, validate_name

from .sections import ProjectList


BG_WINDOW = "#1a1a1a"


class ProjectManagerView(ctk.CTkToplevel):
    """مدیر پروژه‌ها"""

    def __init__(self, master=None, on_close=None, on_project_change=None):
        super().__init__(master)
        self.on_close = on_close
        self.on_project_change = on_project_change

        self.title("📦 Project Manager — مدیریت پروژه‌ها")
        self.geometry("720x780")
        self.minsize(620, 600)
        self.configure(fg_color=BG_WINDOW)

        # ═══ State ═══
        self.store = SchemaStore()
        self.seeder = SchemaSeeder(self.store)
        self.active_project = self.store.get_active_project()

        # ═══ Layout ═══
        self._build_layout()
        self._load_all()

        self.after(50, self.focus_force)
        self.protocol("WM_DELETE_WINDOW", self._on_close_window)

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.project_list = ProjectList(
            self,
            on_select=self._on_project_action,
            on_activate=self._on_activate_project,
        )
        self.project_list.grid(row=0, column=0, sticky="nsew",
                                padx=10, pady=(10, 5))

        self._build_bottom_bar()

    def _build_bottom_bar(self):
        bar = ctk.CTkFrame(self, fg_color="#181818", height=60, corner_radius=6)
        bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))
        bar.grid_propagate(False)

        ctk.CTkButton(
            bar, text="➕  پروژه جدید",
            width=160, height=38,
            fg_color="#0d6efd", hover_color="#0b5ed7",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_add_project,
        ).pack(side="left", padx=(10, 6), pady=11)

        ctk.CTkButton(
            bar, text="🏠  بستن",
            width=120, height=38,
            fg_color="#dc3545", hover_color="#b02a37",
            font=ctk.CTkFont(size=13),
            command=self._on_close_window,
        ).pack(side="right", padx=(6, 10), pady=11)

        self.status_lbl = ctk.CTkLabel(
            bar, text="", text_color="#aaa",
            font=ctk.CTkFont(size=11),
        )
        self.status_lbl.pack(side="right", padx=14)

    # ═════════════════════════════════════════════
    def _load_all(self):
        projects = self.store.list_projects()
        stats = {p.id: self.store.project_stats(p.id) for p in projects}

        self.active_project = self.store.get_active_project()
        self.project_list.load(projects, stats, self.active_project.id)

        name = self.active_project.fa_name or self.active_project.name
        self._set_status(f"پروژه‌ی فعال: {name}")

    def _on_activate_project(self, project_id: int):
        p = self.store.get_project(project_id)
        if not p:
            return

        self.store.set_active_project(project_id)
        self._load_all()

        name = p.fa_name or p.name
        self._set_status(f"✅ فعال شد: {name}")

        if self.on_project_change:
            try:
                self.on_project_change(project_id)
            except Exception as e:
                print(f"⚠️ callback error: {e}")

    def _on_project_action(self, project_id: int, action: str):
        if action == "edit":
            self._edit_project(project_id)
        elif action == "delete":
            self._delete_project(project_id)
        elif action == "clone":
            self._clone_project(project_id)

    def _on_add_project(self):
        dialog = _ProjectDialog(self, mode="add")
        self.wait_window(dialog)

        if dialog.result:
            name, fa_name, description = dialog.result

            if self.store.project_exists(name):
                messagebox.showwarning(
                    "نام تکراری",
                    f"پروژه‌ای با نام «{name}» از قبل وجود داره",
                    parent=self,
                )
                return

            self.store.create_project(name, fa_name, description)
            self._load_all()
            self._set_status(f"✅ پروژه {fa_name or name} ساخته شد")

    def _edit_project(self, project_id: int):
        p = self.store.get_project(project_id)
        if not p:
            return

        dialog = _ProjectDialog(self, mode="edit", project=p)
        self.wait_window(dialog)

        if dialog.result:
            name, fa_name, description = dialog.result

            if self.store.project_exists(name, exclude_id=p.id):
                messagebox.showwarning(
                    "نام تکراری",
                    f"پروژه‌ای با نام «{name}» از قبل وجود داره",
                    parent=self,
                )
                return

            p.name = name
            p.fa_name = fa_name
            p.description = description
            self.store.update_project(p)
            self._load_all()
            self._set_status(f"✏ {fa_name or name} ویرایش شد")

    def _delete_project(self, project_id: int):
        p = self.store.get_project(project_id)
        if not p:
            return

        if p.is_default:
            messagebox.showwarning(
                "پروژه‌ی پیش‌فرض",
                "پروژه‌ی پیش‌فرض رو نمی‌شه حذف کرد",
                parent=self,
            )
            return

        stats = self.store.project_stats(project_id)
        msg = (
            f"پروژه‌ی «{p.fa_name or p.name}» حذف بشه؟\n\n"
            f"شامل {stats['tables']} جدول، {stats['groups']} گروه و "
            f"{stats['columns']} ستون.\n\n"
            f"⚠️ همه‌ی این‌ها برای همیشه پاک می‌شن!"
        )
        if not messagebox.askyesno("حذف پروژه", msg, parent=self):
            return

        was_active = (p.id == self.active_project.id)
        self.store.delete_project(project_id)

        if was_active:
            default = self.store.get_or_create_default_project()
            self.store.set_active_project(default.id)

        self._load_all()
        self._set_status("🗑 پروژه حذف شد")

    def _clone_project(self, project_id: int):
        """کپی پروژه + جداولش"""
        src = self.store.get_project(project_id)
        if not src:
            return

        dialog = _ProjectDialog(
            self, mode="add",
            default_name=f"{src.name}_copy",
            default_fa=f"{src.fa_name or src.name} (کپی)",
        )
        self.wait_window(dialog)

        if not dialog.result:
            return

        name, fa_name, description = dialog.result

        if self.store.project_exists(name):
            messagebox.showwarning("نام تکراری",
                                   f"پروژه‌ای با نام «{name}» هست", parent=self)
            return

        # ساخت پروژه‌ی جدید
        new_p = self.store.create_project(name, fa_name, description)

        # کپی گروه‌ها
        src_groups = self.store.list_groups(project_id)
        group_map = {}
        for g in src_groups:
            from src.models.custom_schema import TableGroup
            new_g = TableGroup(
                project_id=new_p.id,
                name=g.name, fa_name=g.fa_name,
                color=g.color, icon=g.icon,
                order_index=g.order_index,
                is_default=False,
            )
            saved = self.store.save_group(new_g)
            group_map[g.id] = saved.id

        # کپی جداول
        src_tables = self.store.list_tables(project_id)
        for t in src_tables:
            t.id = None
            t.project_id = new_p.id
            t.group_id = group_map.get(t.group_id) if t.group_id else None
            t.is_default = False

            for c in t.columns:
                c.id = None
                c.table_id = None

            self.store.save_table(t)

        self._load_all()
        self._set_status(f"📋 {fa_name or name} کپی شد")

    def _on_close_window(self):
        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass
        self.destroy()

    def _set_status(self, text: str):
        self.status_lbl.configure(text=text)


# ═══════════════════════════════════════════════════════════
# دیالوگ پروژه (ساخت / ویرایش)
# ═══════════════════════════════════════════════════════════
class _ProjectDialog(ctk.CTkToplevel):
    """دیالوگ ساخت/ویرایش پروژه"""

    def __init__(self, master, mode: str = "add",
                 project: Project | None = None,
                 default_name: str = "",
                 default_fa: str = ""):
        super().__init__(master)
        self.result: tuple[str, str, str] | None = None
        self.mode = mode
        self.project = project

        title = "➕  پروژه جدید" if mode == "add" else "✏  ویرایش پروژه"
        self.title(title.replace("➕  ", "").replace("✏  ", ""))
        self.geometry("480x400")
        self.resizable(False, False)
        self.configure(fg_color="#1e1e1e")
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(self, text=title,
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(pady=(20, 16))

        # ─── نام EN ───
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=24, pady=4)
        ctk.CTkLabel(row1, text="🇬🇧 نام (EN):",
                     width=110, anchor="w",
                     text_color="#0d6efd",
                     font=ctk.CTkFont(weight="bold")).pack(side="left")
        self.name_var = ctk.StringVar(
            value=project.name if project else default_name or "new_project"
        )
        ctk.CTkEntry(row1, textvariable=self.name_var,
                     height=32).pack(side="left", fill="x", expand=True)

        # ─── نام FA ───
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=24, pady=4)
        ctk.CTkLabel(row2, text="🇮🇷 نام (FA):",
                     width=110, anchor="w",
                     text_color="#198754",
                     font=ctk.CTkFont(weight="bold")).pack(side="left")
        self.fa_var = ctk.StringVar(
            value=project.fa_name if project else default_fa or "پروژه‌ی جدید"
        )
        ctk.CTkEntry(row2, textvariable=self.fa_var,
                     height=32).pack(side="left", fill="x", expand=True)

        # ─── توضیحات ───
        row3 = ctk.CTkFrame(self, fg_color="transparent")
        row3.pack(fill="x", padx=24, pady=4)
        ctk.CTkLabel(row3, text="توضیحات:",
                     width=110, anchor="w").pack(side="left")
        self.desc_var = ctk.StringVar(
            value=project.description if project else ""
        )
        ctk.CTkEntry(row3, textvariable=self.desc_var,
                     height=32).pack(side="left", fill="x", expand=True)

        # ─── راهنما ───
        ctk.CTkLabel(
            self,
            text="⚠️ نام (EN) باید یکتا باشه و فقط شامل a-z، 0-9 و _",
            text_color="#888",
            font=ctk.CTkFont(size=10),
        ).pack(pady=(10, 4))

        # ─── دکمه‌ها ───
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=24, pady=(16, 20))

        label = "ساخت" if mode == "add" else "ذخیره"
        color = "#198754" if mode == "add" else "#0d6efd"

        ctk.CTkButton(btns, text=label,
                      fg_color=color,
                      hover_color="#146c43" if mode == "add" else "#0b5ed7",
                      width=120, height=38,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._ok).pack(side="right", padx=(6, 0))

        ctk.CTkButton(btns, text="انصراف",
                      fg_color="#444", hover_color="#555",
                      width=100, height=38,
                      command=self.destroy).pack(side="right")

        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())
        self.after(50, self.focus_force)

    def _ok(self):
        name = self.name_var.get().strip()
        fa_name = self.fa_var.get().strip()
        description = self.desc_var.get().strip()

        ok, msg = validate_name(name)
        if not ok:
            messagebox.showwarning("نام نامعتبر", msg, parent=self)
            return

        self.result = (name, fa_name, description)
        self.destroy()