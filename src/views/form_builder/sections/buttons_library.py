# src/views/form_builder/sections/buttons_library.py
"""
کتابخانه دکمه‌ها
─────────────────────────────────
• checkbox برای افزودن/حذف دکمه از Canvas
• ✏ برای ویرایش (مودال)
• ▲▼ برای ترتیب اجرا
• 🗑 برای حذف کامل
"""

import customtkinter as ctk
from tkinter import messagebox

from src.models.form_schema import (
    FormPage, ActionButton,
    ACTION_META, action_meta,
)
from src.services.payload_resolver import suggest_payload
from .button_editor_dialog import ButtonEditorDialog


# ─── رنگ‌بندی ───
BG_PANEL = "#232323"
BG_LIST  = "#1a1a1a"
ROW_BG   = "#2e2e2e"
ROW_SEL  = "#1f3a5f"
ROW_OFF  = "#1e1e1e"   # اگه غیرفعال

METHOD_COLORS = {
    "GET":    "#0d6efd",
    "POST":   "#198754",
    "PUT":    "#fd7e14",
    "PATCH":  "#6f42c1",
    "DELETE": "#dc3545",
}


# ═══════════════════════════════════════════════════════════
# LibraryRow — یک ردیف دکمه در کتابخانه
# ═══════════════════════════════════════════════════════════
class LibraryRow(ctk.CTkFrame):
    """یک ردیف دکمه در کتابخانه"""

    def __init__(self, master, action: ActionButton,
                 on_toggle=None, on_edit=None,
                 on_move_up=None, on_move_down=None,
                 on_delete=None, on_select=None):
        super().__init__(master, fg_color=ROW_BG, corner_radius=6)
        self.action = action
        self.on_toggle = on_toggle
        self.on_edit = on_edit

        # ═══ چک‌باکس ═══
        self.enabled_var = ctk.BooleanVar(value=action.enabled)
        cb = ctk.CTkCheckBox(
            self,
            text="",
            variable=self.enabled_var,
            width=20,
            checkbox_width=18,
            checkbox_height=18,
            command=self._on_cb_toggle,
        )
        cb.pack(side="left", padx=(8, 4), pady=6)

        # ═══ آیکون ═══
        meta = action_meta(action.action)
        ctk.CTkLabel(
            self,
            text=meta["icon"],
            width=22,
            font=ctk.CTkFont(size=14),
        ).pack(side="left", padx=(0, 2))

        # ═══ شماره ترتیب ═══
        ctk.CTkLabel(
            self,
            text=f"#{action.order + 1}",
            width=26,
            text_color="#aaa",
            font=ctk.CTkFont(size=10, weight="bold"),
        ).pack(side="left", padx=(0, 4))

        # ═══ اطلاعات ═══
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, pady=4)

        # سطر اول: برچسب
        top_line = ctk.CTkFrame(info, fg_color="transparent")
        top_line.pack(fill="x")

        ctk.CTkLabel(
            top_line,
            text=action.label,
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left")

        # badge payload
        if action.payload_fields:
            ctk.CTkLabel(
                top_line,
                text=f"📦 {len(action.payload_fields)}",
                text_color="#9ecbff",
                font=ctk.CTkFont(size=9),
            ).pack(side="left", padx=4)
        else:
            ctk.CTkLabel(
                top_line,
                text="📦 auto",
                text_color="#7bd88f",
                font=ctk.CTkFont(size=9),
            ).pack(side="left", padx=4)

        # سطر دوم: method + endpoint
        meta_row = ctk.CTkFrame(info, fg_color="transparent")
        meta_row.pack(fill="x")

        ctk.CTkLabel(
            meta_row,
            text=action.method,
            fg_color=METHOD_COLORS.get(action.method, "#666"),
            corner_radius=3,
            width=46,
            height=14,
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="white",
        ).pack(side="left", padx=(0, 4))

        ctk.CTkLabel(
            meta_row,
            text=action.endpoint,
            text_color="#9ecbff",
            font=ctk.CTkFont(size=9),
            anchor="w",
        ).pack(side="left", fill="x")

        # ═══ دکمه‌های عملیات ═══
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(side="right", padx=4)

        # ✏ ویرایش
        ctk.CTkButton(
            actions,
            text="✏",
            width=24, height=24,
            fg_color="#0d6efd", hover_color="#0b5ed7",
            font=ctk.CTkFont(size=11),
            command=lambda: on_edit and on_edit(action),
        ).pack(pady=(0, 1))

        # ▲▼
        arrows = ctk.CTkFrame(actions, fg_color="transparent")
        arrows.pack()

        ctk.CTkButton(
            arrows,
            text="▲",
            width=18, height=18,
            fg_color="#444", hover_color="#555",
            font=ctk.CTkFont(size=8),
            command=lambda: on_move_up and on_move_up(action),
        ).pack(side="left", padx=1)

        ctk.CTkButton(
            arrows,
            text="▼",
            width=18, height=18,
            fg_color="#444", hover_color="#555",
            font=ctk.CTkFont(size=8),
            command=lambda: on_move_down and on_move_down(action),
        ).pack(side="left", padx=1)

        # 🗑 حذف
        ctk.CTkButton(
            actions,
            text="🗑",
            width=24, height=20,
            fg_color="#6c1f1f", hover_color="#8a2828",
            font=ctk.CTkFont(size=10),
            command=lambda: on_delete and on_delete(action),
        ).pack(pady=(1, 0))

        # ═══ رنگ ردیف بر اساس enabled ═══
        self._update_row_color()

        # ═══ کلیک روی ردیف → انتخاب ═══
        for w in [self, info] + list(info.winfo_children()) + list(top_line.winfo_children()) + list(meta_row.winfo_children()):
            w.bind("<Button-1>", lambda e: on_select and on_select(action))

    # ─────────────────────────────────────────
    def _on_cb_toggle(self):
        self.action.enabled = self.enabled_var.get()
        self._update_row_color()
        if self.on_toggle:
            self.on_toggle(self.action)

    def _update_row_color(self):
        if self.action.enabled:
            self.configure(fg_color=ROW_BG)
        else:
            self.configure(fg_color=ROW_OFF)


# ═══════════════════════════════════════════════════════════
# ButtonsLibrary — پنل کتابخانه
# ═══════════════════════════════════════════════════════════
class ButtonsLibrary(ctk.CTkFrame):
    """پنل کتابخانه دکمه‌ها"""

    def __init__(self, master, form_page: FormPage,
                 on_run=None, on_canvas_refresh=None):
        super().__init__(master, fg_color=BG_PANEL, corner_radius=8)
        self.form_page = form_page
        self.on_run = on_run
        self.on_canvas_refresh = on_canvas_refresh   # callback برای آپدیت Canvas
        self._row_widgets: list[LibraryRow] = []
        self._selected_action_id: str | None = None

        # ═══ هدر ═══
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkLabel(
            header,
            text="🔘 کتابخانه دکمه‌ها",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        self.count_lbl = ctk.CTkLabel(
            header,
            text="",
            text_color="#888",
            font=ctk.CTkFont(size=11),
        )
        self.count_lbl.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(
            self,
            text="✅ = روی Canvas | ✏ = ویرایش | ▲▼ = ترتیب اجرا",
            text_color="#777",
            font=ctk.CTkFont(size=10),
        ).pack(anchor="w", padx=12, pady=(0, 6))

        # ═══ لیست دکمه‌ها ═══
        self.listbox = ctk.CTkScrollableFrame(self, fg_color=BG_LIST)
        self.listbox.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        self._render()

        # ═══ دکمه‌های پایین ═══
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=8, pady=(0, 8))

        # ➕ افزودن دکمه دلخواه
        ctk.CTkButton(
            bottom,
            text="➕  افزودن دکمه",
            fg_color="#444", hover_color="#555",
            height=30,
            font=ctk.CTkFont(size=11),
            command=self._add_custom_button,
        ).pack(fill="x", pady=(0, 4))

        # ▶ اجرا
        ctk.CTkButton(
            bottom,
            text="▶  اجرای زنجیره (Mock)",
            fg_color="#198754", hover_color="#146c43",
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_run_click,
        ).pack(fill="x")

    # ═════════════════════════════════════════════
    def _render(self):
        for w in self.listbox.winfo_children():
            w.destroy()
        self._row_widgets.clear()

        sorted_buttons = sorted(self.form_page.buttons, key=lambda a: a.order)

        for i, action in enumerate(sorted_buttons):
            action.order = i

            row = LibraryRow(
                self.listbox,
                action,
                on_toggle=self._on_toggle,
                on_edit=self._on_edit,
                on_move_up=self._move_up,
                on_move_down=self._move_down,
                on_delete=self._on_delete,
                on_select=self._on_select,
            )
            row.pack(fill="x", pady=3, padx=2)

            if action.id == self._selected_action_id:
                row.configure(fg_color=ROW_SEL)

            self._row_widgets.append(row)

        self._update_count()

    def _update_count(self):
        total = len(self.form_page.buttons)
        enabled = sum(1 for b in self.form_page.buttons if b.enabled)
        self.count_lbl.configure(text=f"({enabled}/{total})")

    # ═════════════════════════════════════════════
    # رویدادها
    # ═════════════════════════════════════════════
    def _on_select(self, action: ActionButton):
        self._selected_action_id = action.id
        for row in self._row_widgets:
            if row.action.id == action.id:
                row.configure(fg_color=ROW_SEL)
            else:
                row._update_row_color()

    def _on_toggle(self, action: ActionButton):
        """چک‌باکس روشن/خاموش شد"""
        self._update_count()
        if self.on_canvas_refresh:
            self.on_canvas_refresh()

    def _on_edit(self, action: ActionButton):
        """✏ → باز کردن مودال ویرایش"""
        ButtonEditorDialog(
            self.winfo_toplevel(),
            self.form_page,
            action,
            on_save=self._on_editor_saved,
        )

    def _on_editor_saved(self, action: ActionButton):
        """بعد از ذخیره در مودال"""
        self._render()
        if self.on_canvas_refresh:
            self.on_canvas_refresh()

    def _move_up(self, action: ActionButton):
        buttons = sorted(self.form_page.buttons, key=lambda a: a.order)
        idx = next((i for i, b in enumerate(buttons) if b.id == action.id), -1)
        if idx <= 0:
            return

        buttons[idx - 1].order, buttons[idx].order = buttons[idx].order, buttons[idx - 1].order
        self._render()

        if self.on_canvas_refresh:
            self.on_canvas_refresh()

    def _move_down(self, action: ActionButton):
        buttons = sorted(self.form_page.buttons, key=lambda a: a.order)
        idx = next((i for i, b in enumerate(buttons) if b.id == action.id), -1)
        if idx < 0 or idx >= len(buttons) - 1:
            return

        buttons[idx + 1].order, buttons[idx].order = buttons[idx].order, buttons[idx + 1].order
        self._render()

        if self.on_canvas_refresh:
            self.on_canvas_refresh()

    def _on_delete(self, action: ActionButton):
        """🗑 → حذف کامل"""
        if not messagebox.askyesno(
            "حذف دکمه",
            f"دکمه «{action.label}» کاملاً حذف بشه؟",
            parent=self,
        ):
            return

        self.form_page.remove_button(action.id)
        self.form_page.reorder_buttons()
        self._render()

        if self.on_canvas_refresh:
            self.on_canvas_refresh()

    def _add_custom_button(self):
        """افزودن دکمه‌ی دلخواه"""
        import uuid
        new_action = ActionButton(
            id=str(uuid.uuid4())[:8],
            label="دکمه جدید",
            action="custom",
            method="POST",
            endpoint=f"/api/{self.form_page.table}",
            order=len(self.form_page.buttons),
            x=30 + len(self.form_page.buttons) * 130,
            y=520,
            description="",
        )
        self.form_page.buttons.append(new_action)
        self._render()

        if self.on_canvas_refresh:
            self.on_canvas_refresh()

        # بلافاصله مودال ویرایش باز بشه
        self._on_edit(new_action)

    # ═════════════════════════════════════════════
    def _on_run_click(self):
        if self.on_run:
            self.on_run(self.form_page)

    # ═════════════════════════════════════════════
    def set_form(self, form_page: FormPage):
        """بارگذاری فرم جدید"""
        self.form_page = form_page
        self._selected_action_id = None
        self._render()