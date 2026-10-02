# src/views/main_view/sections/header.py
"""
HeaderSection — هدر بالای پنجره
─────────────────────────────────
"""

import customtkinter as ctk


BG_HEADER   = "#161616"
FG_NORM     = "#2e2e2e"
FG_HOV      = "#3a3a3a"
FG_DISCONN  = "#dc3545"
FG_CHANGE   = "#0d6efd"


class HeaderSection(ctk.CTkFrame):
    """هدر اصلی"""

    def __init__(self, master, on_connect=None, on_disconnect=None,
                 on_quick_connect=None):
        super().__init__(master, fg_color=BG_HEADER, height=70, corner_radius=0)
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_quick_connect = on_quick_connect

        self.pack_propagate(False)

        # ═══ چپ: لوگو + عنوان + پروژه ═══
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", padx=(18, 0), pady=10)

        ctk.CTkLabel(
            left, text="⚙️",
            font=ctk.CTkFont(size=26),
        ).pack(side="left", padx=(0, 8))

        title_box = ctk.CTkFrame(left, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box, text="Py App Maker",
            font=ctk.CTkFont(size=17, weight="bold"),
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box, text="Database Schema Explorer",
            font=ctk.CTkFont(size=11),
            text_color="#888", anchor="w",
        ).pack(anchor="w")

        # ⭐ نام پروژه‌ی فعال
        self.project_lbl = ctk.CTkLabel(
            left,
            text="📦 —",
            text_color="#fd7e14",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.project_lbl.pack(side="left", padx=(20, 0))

        # ═══ راست ═══
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", padx=(0, 18), pady=10)

        self.status_dot = ctk.CTkLabel(
            right,
            text="⚪  متصل نیست",
            font=ctk.CTkFont(size=11),
            text_color="#888",
        )
        self.status_dot.pack(side="left", padx=(0, 12))

        self.btn_disconnect = ctk.CTkButton(
            right, text="🔌  قطع اتصال",
            width=110, height=34,
            fg_color=FG_DISCONN, hover_color="#b02a37",
            font=ctk.CTkFont(size=12),
            command=self._on_disconnect,
        )
        self.btn_disconnect.pack(side="left", padx=3)

        self.btn_change = ctk.CTkButton(
            right, text="🔄  تغییر اتصال",
            width=130, height=34,
            fg_color=FG_CHANGE, hover_color="#0b5ed7",
            font=ctk.CTkFont(size=12),
            command=self._on_connect,
        )
        self.btn_change.pack(side="left", padx=3)

    # ═════════════════════════════════════════════
    def _on_connect(self):
        if self.on_connect:
            self.on_connect()

    def _on_disconnect(self):
        if self.on_disconnect:
            self.on_disconnect()

    # ═════════════════════════════════════════════
    def set_connected(self, connected: bool, db_name: str = ""):
        if connected:
            self.status_dot.configure(
                text=f"🟢  متصل به {db_name}" if db_name else "🟢  متصل",
                text_color="#7bd88f",
            )
            self.btn_disconnect.configure(state="normal")
        else:
            self.status_dot.configure(text="⚪  متصل نیست", text_color="#888")
            self.btn_disconnect.configure(state="disabled")

    def set_active_project(self, project):
        """آپدیت نام پروژه‌ی فعال توی هدر"""
        if project is None:
            self.project_lbl.configure(text="📦 —")
            return
        name = project.fa_name or project.name
        self.project_lbl.configure(text=f"📦 {name}")