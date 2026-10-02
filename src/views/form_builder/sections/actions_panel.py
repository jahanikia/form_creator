# src/views/form_builder/sections/actions_panel.py
"""
پنل دکمه‌های فرم (CRUD + ترتیب اجرا)
─────────────────────────────────────────
• نمایش دکمه‌ها با ترتیب فعلی
• جابجایی ترتیب با ▲ / ▼
• حذف / افزودن دکمه
• اجرای زنجیره با Mock API
• همگام‌سازی با Canvas از طریق callback (on_reorder)
"""

import customtkinter as ctk
from src.models.form_schema import ActionButton


# ─── رنگ‌بندی ───
BG_PANEL = "#232323"
BG_LIST  = "#1a1a1a"
ROW_BG   = "#2e2e2e"
ROW_SEL  = "#1f3a5f"

# ─── رنگ بر اساس HTTP method ───
METHOD_COLORS = {
    "GET":    "#0d6efd",
    "POST":   "#198754",
    "PUT":    "#fd7e14",
    "PATCH":  "#6f42c1",
    "DELETE": "#dc3545",
}

# ─── آیکون بر اساس action ───
ACTION_ICONS = {
    "create": "➕",
    "read":   "👁",
    "update": "✏️",
    "delete": "🗑",
    "custom": "⚙️",
}


# ═══════════════════════════════════════════════════════════
# ActionRow — یک ردیف دکمه در پنل
# ═══════════════════════════════════════════════════════════
class ActionRow(ctk.CTkFrame):
    """یک ردیف دکمه در پنل"""

    def __init__(self, master, action: ActionButton,
                 on_select=None, on_move_up=None, on_move_down=None):
        super().__init__(master, fg_color=ROW_BG, corner_radius=6)
        self.action = action
        self.on_select = on_select
        self._selected = False

        # ─── آیکون ───
        icon = ACTION_ICONS.get(action.action, "⚙️")
        ctk.CTkLabel(
            self,
            text=icon,
            width=24,
            font=ctk.CTkFont(size=14),
        ).pack(side="left", padx=(6, 2), pady=6)

        # ─── شماره ترتیب ───
        ctk.CTkLabel(
            self,
            text=f"#{action.order + 1}",
            width=28,
            text_color="#aaa",
            font=ctk.CTkFont(size=10, weight="bold"),
        ).pack(side="left", padx=(0, 4))

        # ─── اطلاعات اکشن ───
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, pady=4)

        # سطر اول: برچسب
        ctk.CTkLabel(
            info,
            text=action.label,
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(fill="x")

        # سطر دوم: method + endpoint
        meta = ctk.CTkFrame(info, fg_color="transparent")
        meta.pack(fill="x")

        ctk.CTkLabel(
            meta,
            text=action.method,
            fg_color=METHOD_COLORS.get(action.method, "#666"),
            corner_radius=3,
            width=48,
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="white",
        ).pack(side="left", padx=(0, 4))

        ctk.CTkLabel(
            meta,
            text=action.endpoint,
            text_color="#9ecbff",
            font=ctk.CTkFont(size=9),
            anchor="w",
        ).pack(side="left", fill="x")

        # ─── دکمه‌های ↑↓ ───
        arrows = ctk.CTkFrame(self, fg_color="transparent")
        arrows.pack(side="right", padx=4)

        ctk.CTkButton(
            arrows,
            text="▲",
            width=22, height=20,
            fg_color="#444", hover_color="#555",
            font=ctk.CTkFont(size=9),
            command=lambda: on_move_up and on_move_up(action),
        ).pack(pady=(0, 1))

        ctk.CTkButton(
            arrows,
            text="▼",
            width=22, height=20,
            fg_color="#444", hover_color="#555",
            font=ctk.CTkFont(size=9),
            command=lambda: on_move_down and on_move_down(action),
        ).pack()

        # ─── کلیک روی کل ردیف → انتخاب ───
        for w in [self, info, meta] + list(info.winfo_children()) + list(meta.winfo_children()):
            w.bind("<Button-1>", lambda e: on_select and on_select(action))

    def set_selected(self, selected: bool):
        self._selected = selected
        self.configure(fg_color=ROW_SEL if selected else ROW_BG)


# ═══════════════════════════════════════════════════════════
# ActionsPanel — پنل دکمه‌های CRUD
# ═══════════════════════════════════════════════════════════
class ActionsPanel(ctk.CTkFrame):
    """پنل دکمه‌های CRUD با همگام‌سازی Canvas"""

    def __init__(self, master, form_page, on_run=None, on_reorder=None):
        super().__init__(master, fg_color=BG_PANEL, corner_radius=8)
        self.form_page = form_page
        self.on_run = on_run
        self.on_reorder = on_reorder          # ⭐ callback برای Canvas
        self._row_widgets: list[ActionRow] = []
        self._selected_action_id: str | None = None

        # ═══ هدر ═══
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkLabel(
            header,
            text="🔘 دکمه‌ها",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        self.count_lbl = ctk.CTkLabel(
            header,
            text=f"({len(form_page.buttons)})",
            text_color="#888",
            font=ctk.CTkFont(size=11),
        )
        self.count_lbl.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(
            self,
            text="ترتیب با ▲▼ — موقعیت مکانی روی Canvas با Drag",
            text_color="#777",
            font=ctk.CTkFont(size=10),
        ).pack(anchor="w", padx=12, pady=(0, 6))

        # ═══ لیست دکمه‌ها ═══
        self.listbox = ctk.CTkScrollableFrame(self, fg_color=BG_LIST)
        self.listbox.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        self._render_buttons()

        # ═══ دکمه اجرا ═══
        self.run_btn = ctk.CTkButton(
            self,
            text="▶  اجرای زنجیره (Mock)",
            fg_color="#198754",
            hover_color="#146c43",
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_run_click,
        )
        self.run_btn.pack(fill="x", padx=8, pady=(0, 8))

    # ═════════════════════════════════════════════
    # رندر لیست
    # ═════════════════════════════════════════════
    def _render_buttons(self):
        for w in self.listbox.winfo_children():
            w.destroy()
        self._row_widgets.clear()

        sorted_buttons = sorted(self.form_page.buttons, key=lambda a: a.order)

        for i, action in enumerate(sorted_buttons):
            # نرمال‌سازی order (0, 1, 2, ...)
            action.order = i

            row = ActionRow(
                self.listbox,
                action,
                on_select=self._on_row_select,
                on_move_up=self._move_up,
                on_move_down=self._move_down,
            )
            row.pack(fill="x", pady=3, padx=2)

            if action.id == self._selected_action_id:
                row.set_selected(True)

            self._row_widgets.append(row)

        self.count_lbl.configure(text=f"({len(sorted_buttons)})")

    # ═════════════════════════════════════════════
    # انتخاب
    # ═════════════════════════════════════════════
    def _on_row_select(self, action: ActionButton):
        self._selected_action_id = action.id
        for row in self._row_widgets:
            row.set_selected(row.action.id == action.id)

    # ═════════════════════════════════════════════
    # جابجایی ترتیب
    # ═════════════════════════════════════════════
    def _move_up(self, action: ActionButton):
        buttons = sorted(self.form_page.buttons, key=lambda a: a.order)
        idx = next(i for i, b in enumerate(buttons) if b.id == action.id)
        if idx == 0:
            return   # اولین هست، نمی‌تونه بالاتر بره

        # جابجایی order با قبلی
        buttons[idx - 1].order, buttons[idx].order = buttons[idx].order, buttons[idx - 1].order
        self._render_buttons()

        # ⭐ همگام‌سازی با Canvas
        if self.on_reorder:
            self.on_reorder()

    def _move_down(self, action: ActionButton):
        buttons = sorted(self.form_page.buttons, key=lambda a: a.order)
        idx = next(i for i, b in enumerate(buttons) if b.id == action.id)
        if idx == len(buttons) - 1:
            return   # آخرین هست

        # جابجایی order با بعدی
        buttons[idx + 1].order, buttons[idx].order = buttons[idx].order, buttons[idx + 1].order
        self._render_buttons()

        # ⭐ همگام‌سازی با Canvas
        if self.on_reorder:
            self.on_reorder()

    # ═════════════════════════════════════════════
    # اجرا
    # ═════════════════════════════════════════════
    def _on_run_click(self):
        if self.on_run:
            self.on_run(self.form_page)

    # ═════════════════════════════════════════════
    # تغییر فرم
    # ═════════════════════════════════════════════
    def set_form(self, form_page):
        """بارگذاری یه فرم جدید"""
        self.form_page = form_page
        self._selected_action_id = None
        self._render_buttons()