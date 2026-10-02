# src/views/main_view/sections/menu_bar.py
"""
MenuBarSection — نوار ابزار
─────────────────────────────────
"""

import customtkinter as ctk


BG_MENU = "#1a1a1a"
FG_NORM = "#2e2e2e"
FG_HOV  = "#3a3a3a"

FG_PRIMARY = "#0d6efd"
FG_SUCCESS = "#198754"
FG_WARNING = "#fd7e14"
FG_PURPLE  = "#6f42c1"
FG_PINK    = "#c2185b"


class MenuBarSection(ctk.CTkFrame):
    """نوار ابزار اصلی"""

    def __init__(self, master,
                 on_project_manager=None,
                 on_schema_designer=None,
                 on_form_builder=None,
                 on_generate=None,
                 on_auth_setup=None,
                 on_tests=None,
                 on_generate_flutter=None,
                 on_generate_docs=None,
                 on_view_docs=None,
                 on_export_json=None,
                 on_export_sql=None,
                 on_refresh=None,
                 on_api_tester=None):
        super().__init__(master, fg_color=BG_MENU, height=56, corner_radius=0)
        self.pack_propagate(False)

        # ═══ چپ ═══
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", padx=(14, 0), pady=10)

        # ─── 📦 پروژه‌ها ───
        ctk.CTkButton(
            left,
            text="📦  پروژه‌ها",
            width=130, height=36,
            fg_color=FG_WARNING, hover_color="#e36f0b",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: on_project_manager and on_project_manager(),
        ).pack(side="left", padx=3)

        # ─── 🗄️ Schema Designer ───
        ctk.CTkButton(
            left,
            text="🗄️  Schema Designer",
            width=170, height=36,
            fg_color=FG_PRIMARY, hover_color="#0b5ed7",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: on_schema_designer and on_schema_designer(),
        ).pack(side="left", padx=3)

        # ─── 🎨 Form Builder ───
        ctk.CTkButton(
            left,
            text="🎨  Form Builder",
            width=150, height=36,
            fg_color=FG_PURPLE, hover_color="#5a32a3",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: on_form_builder and on_form_builder(),
        ).pack(side="left", padx=3)

        self._separator(left)

        # ─── ⚡ تولید ───
        ctk.CTkButton(
            left,
            text="⚡  تولید پروژه",
            width=130, height=36,
            fg_color=FG_SUCCESS, hover_color="#146c43",
            font=ctk.CTkFont(size=12),
            command=lambda: on_generate and on_generate(),
        ).pack(side="left", padx=3)

        # ─── 🔐 Auth ───
        ctk.CTkButton(
            left,
            text="🔐  Auth",
            width=90, height=36,
            fg_color="#2e7d32", hover_color="#1b5e20",
            font=ctk.CTkFont(size=12),
            command=lambda: on_auth_setup and on_auth_setup(),
        ).pack(side="left", padx=3)

        # ─── 🧪 Tests ───
        ctk.CTkButton(
            left,
            text="🧪  Tests",
            width=90, height=36,
            fg_color="#7b1fa2", hover_color="#5e1387",
            font=ctk.CTkFont(size=12),
            command=lambda: on_tests and on_tests(),
        ).pack(side="left", padx=3)

        # ─── 📱 Flutter ───
        ctk.CTkButton(
            left,
            text="📱  Flutter",
            width=100, height=36,
            fg_color=FG_PINK, hover_color="#a01548",
            font=ctk.CTkFont(size=12),
            command=lambda: on_generate_flutter and on_generate_flutter(),
        ).pack(side="left", padx=3)

        # ═══ راست ═══
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", padx=(0, 14), pady=10)

        ctk.CTkButton(
            right,
            text="🧪  API Tester",
            width=120, height=36,
            fg_color=FG_NORM, hover_color=FG_HOV,
            font=ctk.CTkFont(size=12),
            command=lambda: on_api_tester and on_api_tester(),
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            right,
            text="📖  مشاهده",
            width=90, height=36,
            fg_color=FG_NORM, hover_color=FG_HOV,
            font=ctk.CTkFont(size=12),
            command=lambda: on_view_docs and on_view_docs(),
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            right,
            text="📝  مستندات",
            width=110, height=36,
            fg_color=FG_NORM, hover_color=FG_HOV,
            font=ctk.CTkFont(size=12),
            command=lambda: on_generate_docs and on_generate_docs(),
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            right,
            text="🔄",
            width=40, height=36,
            fg_color=FG_NORM, hover_color=FG_HOV,
            font=ctk.CTkFont(size=14),
            command=lambda: on_refresh and on_refresh(),
        ).pack(side="left", padx=3)

    @staticmethod
    def _separator(parent):
        ctk.CTkFrame(
            parent,
            fg_color="#444",
            width=1, height=28, corner_radius=0,
        ).pack(side="left", padx=8)