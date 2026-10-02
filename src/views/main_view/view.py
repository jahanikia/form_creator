# src/views/main_view/view.py
"""
MainView — پنجره‌ی اصلی برنامه
─────────────────────────────────
"""

import customtkinter as ctk
from tkinter import messagebox

from src.utils.window_utils import WindowUtils
from src.services.mock_schema import list_tables, get_columns

from .sections import (
    HeaderSection,
    MenuBarSection,
    BodySection,
    StatusBarSection,
)


class MainView(ctk.CTk):
    """پنجره‌ی اصلی"""

    def __init__(self):
        super().__init__()

        # ═══ State ═══
        self.is_connected = False
        self.current_db = ""
        self.current_table: str | None = None
        self.form_builder_window = None
        self.schema_designer_window = None
        self.project_manager_window = None
        self.active_project = None

        # ═══ تنظیمات پنجره ═══
        self.title("Py App Maker — Database Schema Explorer")

        w, h = WindowUtils.calculate_size(
            self,
            desired_width=1440,
            desired_height=860,
            ratio=0.92,
            min_width=1000,
            min_height=650,
        )
        self.geometry(f"{w}x{h}")
        self.minsize(1000, 650)
        WindowUtils.center_window(self, w, h)

        # ═══ ساخت UI ═══
        self._build_ui()

        # ═══ لود پروژه ═══
        self.after(100, self._load_active_project)
        self.after(150, self._load_mock_data)

    # ═════════════════════════════════════════════
    def _build_ui(self):
        # ─── Header ───
        self.header = HeaderSection(
            self,
            on_connect=self._on_connect,
            on_disconnect=self._on_disconnect,
            on_quick_connect=self._on_quick_connect,
        )
        self.header.pack(fill="x", side="top")

        # ─── MenuBar ───
        self.menu_bar = MenuBarSection(
            self,
            on_project_manager=self._open_project_manager,
            on_schema_designer=self._open_schema_designer,
            on_form_builder=self._open_form_builder,
            on_generate=self._on_generate,
            on_auth_setup=self._on_auth_setup,
            on_tests=self._on_tests,
            on_generate_flutter=self._on_generate_flutter,
            on_generate_docs=self._on_generate_docs,
            on_view_docs=self._on_view_docs,
            on_export_json=self._on_export_json,
            on_export_sql=self._on_export_sql,
            on_refresh=self._on_refresh,
            on_api_tester=self._on_api_tester,
        )
        self.menu_bar.pack(fill="x", side="top")

        # ─── StatusBar ───
        self.status_bar = StatusBarSection(self)
        self.status_bar.pack(fill="x", side="bottom")

        # ─── Body ───
        self.body = BodySection(
            self,
            on_table_select=self._on_table_select,
        )
        self.body.pack(fill="both", expand=True, padx=10, pady=10)

    # ═════════════════════════════════════════════
    # پروژه
    # ═════════════════════════════════════════════
    def _load_active_project(self):
        try:
            from src.services.schema_store import SchemaStore
            store = SchemaStore()
            self.active_project = store.get_active_project()

            if hasattr(self.header, "set_active_project"):
                self.header.set_active_project(self.active_project)

            name = self.active_project.fa_name or self.active_project.name
            self.status_bar.set_status(f"📦 پروژه‌ی فعال: {name}")
        except Exception as e:
            print(f"⚠️ خطا در لود پروژه: {e}")

    def _on_project_changed(self, project_id: int):
        """وقتی پروژه عوض شد"""
        try:
            from src.services.schema_store import SchemaStore
            store = SchemaStore()
            project = store.get_project(project_id)
            if not project:
                return

            self.active_project = project

            if hasattr(self.header, "set_active_project"):
                self.header.set_active_project(project)

            name = project.fa_name or project.name
            self.status_bar.set_status(f"📦 پروژه‌ی فعال: {name}")

            # بستن پنجره‌های باز (چون پروژه عوض شده)
            self._close_project_windows()

        except Exception as e:
            print(f"⚠️ خطا در تغییر پروژه: {e}")

    def _close_project_windows(self):
        """بستن Schema Designer و Form Builder (چون پروژه عوض شده)"""
        for attr in ("schema_designer_window", "form_builder_window"):
            win = getattr(self, attr, None)
            if win is not None:
                try:
                    if win.winfo_exists():
                        win.destroy()
                except Exception:
                    pass
                setattr(self, attr, None)

    # ═════════════════════════════════════════════
    def _load_mock_data(self):
        tables = list_tables()
        self.body.load_tables(tables)
        if not self.active_project:
            self.status_bar.set_status(f"🔧 حالت Mock — {len(tables)} جدول")

    # ═════════════════════════════════════════════
    # رویدادهای اتصال
    # ═════════════════════════════════════════════
    def _on_connect(self):
        self.is_connected = True
        self.current_db = "mock_db"
        self.header.set_connected(True, self.current_db)
        self.status_bar.set_status(f"🟢 متصل به {self.current_db} (mock)")

        tables = list_tables()
        self.body.load_tables(tables)
        self.body.clear_detail()

        messagebox.showinfo(
            "اتصال",
            f"به {self.current_db} متصل شدید (mock).\n"
            f"{len(tables)} جدول یافت شد.",
            parent=self,
        )

    def _on_disconnect(self):
        if not self.is_connected:
            return
        if not messagebox.askyesno("قطع اتصال", "اتصال قطع شود؟", parent=self):
            return

        self.is_connected = False
        self.current_db = ""
        self.current_table = None
        self.header.set_connected(False)
        self.body.clear_detail()
        self.status_bar.set_status("⚪ اتصال قطع شد")

    def _on_quick_connect(self):
        self._on_connect()

    # ═════════════════════════════════════════════
    def _on_table_select(self, table_name: str):
        self.current_table = table_name
        cols = get_columns(table_name)
        self.body.show_columns(table_name, cols)
        self.status_bar.set_status(f"📊 {table_name} — {len(cols)} ستون")

    # ═════════════════════════════════════════════
    # Project Manager
    # ═════════════════════════════════════════════
    def _open_project_manager(self):
        from src.views.project_manager import ProjectManagerView

        if self.project_manager_window is not None:
            try:
                if self.project_manager_window.winfo_exists():
                    self.project_manager_window.focus_force()
                    return
            except Exception:
                pass

        self.project_manager_window = ProjectManagerView(
            self,
            on_close=self._on_project_manager_closed,
            on_project_change=self._on_project_changed,
        )
        self.status_bar.set_status("📦 Project Manager باز شد")

    def _on_project_manager_closed(self):
        self.project_manager_window = None
        self.focus_force()

    # ═════════════════════════════════════════════
    # Schema Designer
    # ═════════════════════════════════════════════
    def _open_schema_designer(self):
        from src.views.schema_designer import SchemaDesignerView

        if self.schema_designer_window is not None:
            try:
                if self.schema_designer_window.winfo_exists():
                    self.schema_designer_window.focus_force()
                    return
            except Exception:
                pass

        self.schema_designer_window = SchemaDesignerView(
            self,
            on_close=self._on_schema_designer_closed,
        )
        self.status_bar.set_status("🗄️ Schema Designer باز شد")

    def _on_schema_designer_closed(self):
        self.schema_designer_window = None
        self.focus_force()

    # ═════════════════════════════════════════════
    # Form Builder
    # ═════════════════════════════════════════════
    def _open_form_builder(self):
        from src.views.form_builder import FormBuilderView

        if self.form_builder_window is not None:
            try:
                if self.form_builder_window.winfo_exists():
                    self.form_builder_window.focus_force()
                    return
            except Exception:
                pass

        self.form_builder_window = FormBuilderView(
            self,
            on_close=self._on_form_builder_closed,
        )
        self.status_bar.set_status("🎨 Form Builder باز شد")

    def _on_form_builder_closed(self):
        self.form_builder_window = None
        self.focus_force()

    # ═════════════════════════════════════════════
    # بقیه‌ی دکمه‌ها
    # ═════════════════════════════════════════════
    def _on_generate(self):
        messagebox.showinfo("تولید پروژه", "این قابلیت هنوز پیاده‌سازی نشده.", parent=self)

    def _on_auth_setup(self):
        messagebox.showinfo("Auth Setup", "این قابلیت هنوز پیاده‌سازی نشده.", parent=self)

    def _on_tests(self):
        messagebox.showinfo("Tests", "این قابلیت هنوز پیاده‌سازی نشده.", parent=self)

    def _on_generate_flutter(self):
        messagebox.showinfo("Flutter", "این قابلیت هنوز پیاده‌سازی نشده.", parent=self)

    def _on_generate_docs(self):
        messagebox.showinfo("مستندات", "این قابلیت هنوز پیاده‌سازی نشده.", parent=self)

    def _on_view_docs(self):
        messagebox.showinfo("مشاهده مستندات", "این قابلیت هنوز پیاده‌سازی نشده.", parent=self)

    def _on_export_json(self):
        messagebox.showinfo("Export JSON", "این قابلیت هنوز پیاده‌سازی نشده.", parent=self)

    def _on_export_sql(self):
        messagebox.showinfo("Export SQL", "این قابلیت هنوز پیاده‌سازی نشده.", parent=self)

    def _on_api_tester(self):
        messagebox.showinfo("API Tester", "این قابلیت هنوز پیاده‌سازی نشده.", parent=self)

    def _on_refresh(self):
        if self.is_connected:
            tables = list_tables()
            self.body.load_tables(tables)
            self.body.clear_detail()
            self.status_bar.set_status(f"🔄 تازه‌سازی شد — {len(tables)} جدول")
        else:
            self._load_mock_data()

    # ═════════════════════════════════════════════
    def on_closing(self):
        for attr in ("form_builder_window", "schema_designer_window",
                     "project_manager_window"):
            win = getattr(self, attr, None)
            if win is not None:
                try:
                    if win.winfo_exists():
                        win.destroy()
                except Exception:
                    pass

        if not messagebox.askyesno("خروج", "از برنامه خارج می‌شوید؟", parent=self):
            return

        self.destroy()