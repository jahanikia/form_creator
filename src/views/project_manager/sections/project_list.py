# src/views/project_manager/sections/project_list.py
"""
ProjectList — لیست پروژه‌ها
"""

import customtkinter as ctk


BG_PANEL  = "#232323"
BG_LIST   = "#1a1a1a"
ROW_BG    = "#2e2e2e"
ROW_SEL   = "#0d6efd"
ROW_HOV   = "#3a3a3a"
ROW_ACTIVE = "#1e4d2b"


class ProjectList(ctk.CTkFrame):
    """لیست پروژه‌ها"""

    def __init__(self, master, on_select=None, on_activate=None):
        super().__init__(master, fg_color=BG_PANEL, corner_radius=8)
        self.on_select = on_select
        self.on_activate = on_activate

        self.current_id: int | None = None
        self.active_id: int | None = None
        self._row_widgets: dict[int, ctk.CTkFrame] = {}
        self._projects: list = []
        self._stats: dict[int, dict] = {}

        # ─── هدر ───
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkLabel(
            header, text="📦 پروژه‌ها",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        self.count_lbl = ctk.CTkLabel(
            header, text="(0)", text_color="#888",
            font=ctk.CTkFont(size=11),
        )
        self.count_lbl.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(
            self,
            text="روی «✅ فعال کن» برای سوئیچ پروژه کلیک کنید",
            text_color="#777", font=ctk.CTkFont(size=10),
        ).pack(anchor="w", padx=12, pady=(0, 6))

        # ─── لیست ───
        self.listbox = ctk.CTkScrollableFrame(self, fg_color=BG_LIST)
        self.listbox.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # ═════════════════════════════════════════════
    def load(self, projects: list, stats: dict, active_id: int):
        self._projects = projects
        self._stats = stats
        self.active_id = active_id

        for w in self.listbox.winfo_children():
            w.destroy()
        self._row_widgets.clear()

        if not projects:
            ctk.CTkLabel(
                self.listbox,
                text="\n\n📦  هیچ پروژه‌ای نیست\n\nپروژه‌ی جدید بساز",
                text_color="#666", font=ctk.CTkFont(size=12),
                justify="center",
            ).pack(pady=20)
            self.count_lbl.configure(text="(0)")
            return

        for p in projects:
            self._add_project_card(p, p.id == active_id)

        self.count_lbl.configure(text=f"({len(projects)})")

    def _add_project_card(self, project, is_active: bool):
        card = ctk.CTkFrame(
            self.listbox,
            fg_color=ROW_ACTIVE if is_active else ROW_BG,
            corner_radius=6,
            border_width=2,
            border_color="#198754" if is_active else "#333",
        )
        card.pack(fill="x", pady=4, padx=2)

        # ─── ردیف بالا: آیکون + نام + دکمه فعال ───
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=(8, 2))

        icon = "✅" if is_active else "📦"
        ctk.CTkLabel(
            top, text=icon,
            font=ctk.CTkFont(size=16),
        ).pack(side="left", padx=(0, 6))

        name_box = ctk.CTkFrame(top, fg_color="transparent")
        name_box.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            name_box,
            text=project.fa_name or project.name,
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            name_box,
            text=project.name,
            anchor="w",
            text_color="#888",
            font=ctk.CTkFont(size=10),
        ).pack(anchor="w")

        if not is_active:
            ctk.CTkButton(
                top, text="✅  فعال کن",
                width=90, height=26,
                fg_color="#198754", hover_color="#146c43",
                font=ctk.CTkFont(size=10),
                command=lambda pid=project.id: self._activate(pid),
            ).pack(side="right", padx=(4, 0))
        else:
            ctk.CTkLabel(
                top, text="● فعال",
                text_color="#7bd88f",
                font=ctk.CTkFont(size=10, weight="bold"),
            ).pack(side="right", padx=(4, 0))

        # ─── آمار ───
        stats = self._stats.get(project.id, {})
        stats_text = (
            f"📋 {stats.get('tables', 0)} جدول  •  "
            f"📁 {stats.get('groups', 0)} گروه  •  "
            f"📊 {stats.get('columns', 0)} ستون"
        )
        ctk.CTkLabel(
            card, text=stats_text,
            text_color="#9ecbff",
            font=ctk.CTkFont(size=10),
            anchor="w",
        ).pack(fill="x", padx=10, pady=(2, 2))

        # ─── توضیحات ───
        if project.description:
            ctk.CTkLabel(
                card, text=project.description,
                text_color="#888",
                font=ctk.CTkFont(size=10),
                anchor="w",
                wraplength=380,
                justify="left",
            ).pack(fill="x", padx=10, pady=(0, 4))

        # ─── دکمه‌های عملیات ───
        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(fill="x", padx=8, pady=(0, 8))

        ctk.CTkButton(
            btns, text="✏  ویرایش",
            width=80, height=26,
            fg_color="#444", hover_color="#555",
            font=ctk.CTkFont(size=10),
            command=lambda pid=project.id: self._select(pid, "edit"),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            btns, text="📋  کپی",
            width=80, height=26,
            fg_color="#0d6efd", hover_color="#0b5ed7",
            font=ctk.CTkFont(size=10),
            command=lambda pid=project.id: self._select(pid, "clone"),
        ).pack(side="left", padx=(0, 4))

        if project.is_default:
            ctk.CTkLabel(
                btns, text="🔒 پیش‌فرض",
                text_color="#c97a7a",
                font=ctk.CTkFont(size=10),
            ).pack(side="right")
        else:
            ctk.CTkButton(
                btns, text="🗑",
                width=36, height=26,
                fg_color="#6c1f1f", hover_color="#8a2828",
                font=ctk.CTkFont(size=11),
                command=lambda pid=project.id: self._select(pid, "delete"),
            ).pack(side="right")

        self._row_widgets[project.id] = card

    def _activate(self, project_id: int):
        if self.on_activate:
            self.on_activate(project_id)

    def _select(self, project_id: int, action: str):
        if self.on_select:
            self.on_select(project_id, action)