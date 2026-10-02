# src/views/form_builder/sections/canvas.py
"""
Canvas — بوم طراحی فرم
─────────────────────────────────
• استفاده از tkinter.Frame خام برای container ها
• داخل container ها: ویجت‌های CTk
• callback on_fields_change برای همگام‌سازی با ColumnPanel
• فیلدهای auto_fill: پس‌زمینه سبز + badge
• فیلدهای visible=False: کم‌رنگ + 🚫
• فیلدهای searchable=True: 🔍
• دکمه‌های enabled=False: محو
• دابل‌کلیک دکمه → مودال ویرایش
• راست‌کلیک → منوی rich
"""

import tkinter as tk
import customtkinter as ctk

from src.models.form_schema import (
    FieldElement, ActionButton,
    auto_fill_label, action_meta,
)
from .button_editor_dialog import ButtonEditorDialog


# ─── رنگ‌بندی ───
BG_PANEL        = "#232323"
BG_CANVAS       = "#0f0f0f"

FIELD_BG        = "#2a2a2a"
FIELD_AUTO_BG   = "#1e3a2a"
FIELD_HIDDEN_BG = "#1c1c1c"
FIELD_BORDER    = "#4a4a4a"
FIELD_SEL       = "#0d6efd"

BTN_BG          = "#2e2e2e"
BTN_DISABLED_BG = "#1a1a1a"
BTN_BORDER      = "#444"
BTN_SEL         = "#0d6efd"

GRID_SIZE       = 10

METHOD_COLORS = {
    "GET":    "#0d6efd",
    "POST":   "#198754",
    "PUT":    "#fd7e14",
    "PATCH":  "#6f42c1",
    "DELETE": "#dc3545",
}


class FormCanvas(ctk.CTkFrame):
    """بوم طراحی فرم"""

    def __init__(self, master, form_page, on_fields_change=None):
        super().__init__(master, fg_color=BG_PANEL, corner_radius=8)
        self.form_page = form_page
        self.on_fields_change = on_fields_change
        self._rendered_fields: dict[str, tk.Frame] = {}
        self._rendered_buttons: dict[str, tk.Frame] = {}
        self._selected_id: str | None = None
        self._selected_kind: str | None = None

        # ═══ هدر ═══
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 4))

        self.title_lbl = ctk.CTkLabel(
            header,
            text=f"🎨 Canvas — {form_page.name}",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.title_lbl.pack(side="left")

        ctk.CTkLabel(
            header,
            text="(Drag = جابجایی  |  دابل‌کلیک دکمه = ویرایش  |  راست‌کلیک = منو)",
            text_color="#888",
            font=ctk.CTkFont(size=10),
        ).pack(side="left", padx=10)

        self.count_lbl = ctk.CTkLabel(
            header,
            text="",
            text_color="#888",
            font=ctk.CTkFont(size=11),
        )
        self.count_lbl.pack(side="right")

        # ═══ بوم ═══
        self.canvas = tk.Frame(
            self,
            bg=BG_CANVAS,
            highlightthickness=2,
            highlightbackground="#333",
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # ═══ رندر اولیه ═══
        self.after(50, self._initial_render)

    def _initial_render(self):
        self._render_all_fields()
        self._render_all_buttons()
        self._update_count()

    # ═════════════════════════════════════════════
    # API عمومی
    # ═════════════════════════════════════════════
    def add_field_from_column(self, table: str, col: dict):
        """افزودن فیلد جدید — اگه از قبل هست، فقط انتخابش کن"""
        existing = self.form_page.find_field_by_column(col["name"])
        if existing is not None:
            self._select(existing.id, "field")
            return

        idx = len(self.form_page.fields)
        x = 30 + (idx % 4) * 60
        y = 30 + (idx % 8) * 55

        field = FieldElement.create(
            table=table,
            column=col["name"],
            col_type=col["type"],
            x=x, y=y,
            default=col.get("default"),
            extra=col.get("extra", ""),
        )
        self.form_page.fields.append(field)
        self._render_field(field)
        self._update_count()

        if self.on_fields_change:
            self.on_fields_change()

    def refresh(self):
        for w in list(self._rendered_fields.values()):
            w.destroy()
        for w in list(self._rendered_buttons.values()):
            w.destroy()
        self._rendered_fields.clear()
        self._rendered_buttons.clear()

        self._render_all_fields()
        self._render_all_buttons()
        self._update_count()

    def refresh_buttons(self):
        for w in list(self._rendered_buttons.values()):
            w.destroy()
        self._rendered_buttons.clear()
        self._render_all_buttons()
        self._update_count()

    # ═════════════════════════════════════════════
    # رندر فیلد
    # ═════════════════════════════════════════════
    def _render_all_fields(self):
        for f in self.form_page.fields:
            self._render_field(f)

    def _render_field(self, field: FieldElement):
        is_auto = field.auto_fill is not None
        is_hidden = not field.visible

        if is_hidden:
            bg = FIELD_HIDDEN_BG
        elif is_auto:
            bg = FIELD_AUTO_BG
        else:
            bg = FIELD_BG

        h = field.height + (55 if is_auto else 40)

        container = tk.Frame(
            self.canvas,
            bg=bg,
            highlightthickness=2,
            highlightbackground=FIELD_BORDER,
            highlightcolor=FIELD_BORDER,
        )
        container.place(x=field.x, y=field.y, width=field.width, height=h)

        # ─── هدر ───
        top = ctk.CTkFrame(container, fg_color="transparent", height=20)
        top.pack(fill="x", padx=4, pady=(4, 0))
        top.pack_propagate(False)

        icon = self._icon_for(field.widget_type)
        label_text = f"{icon} {field.label}"
        if field.searchable:
            label_text = f"🔍 {label_text}"
        if is_hidden:
            label_text = f"🚫 {label_text}"

        ctk.CTkLabel(
            top,
            text=label_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
            text_color="#888" if is_hidden else "#ffffff",
        ).pack(side="left")

        ctk.CTkLabel(
            top,
            text=field.column,
            text_color="#888",
            font=ctk.CTkFont(size=9),
            anchor="e",
        ).pack(side="right")

        # ─── ورودی ───
        entry = ctk.CTkEntry(
            container,
            height=26,
            placeholder_text=self._placeholder_for(field.widget_type),
        )

        if is_auto:
            entry.configure(
                state="disabled",
                placeholder_text=f"⚡ {auto_fill_label(field.auto_fill)}",
                fg_color="#173026" if not is_hidden else "#141414",
                text_color="#7bd88f",
            )
        elif is_hidden:
            entry.configure(
                state="disabled",
                placeholder_text="🚫 مخفی",
                fg_color="#141414",
                text_color="#666",
            )

        entry.pack(fill="x", padx=4, pady=(2, 4))

        # ─── نوار auto ───
        if is_auto:
            auto_bar = ctk.CTkFrame(container, fg_color="transparent", height=22)
            auto_bar.pack(fill="x", padx=4, pady=(0, 4))
            auto_bar.pack_propagate(False)

            var = ctk.BooleanVar(value=not is_hidden)

            def toggle_auto(v=var, f=field, e=entry):
                f.auto_fill = f.auto_fill if v.get() else None
                if v.get():
                    e.configure(state="disabled", fg_color="#173026")
                else:
                    e.configure(state="normal", fg_color="#333")

            ctk.CTkCheckBox(
                auto_bar,
                text=auto_fill_label(field.auto_fill),
                variable=var,
                command=toggle_auto,
                font=ctk.CTkFont(size=10),
                text_color="#7bd88f",
                checkbox_width=16,
                checkbox_height=16,
            ).pack(side="left")

        # ─── ذخیره + رویدادها ───
        self._rendered_fields[field.id] = container
        container._field_id = field.id
        container._kind = "field"
        container._offset = None

        drag_targets = [container, top, entry] + list(top.winfo_children())
        for w in drag_targets:
            w.bind("<Button-1>",        lambda e, c=container: self._on_drag_start(e, c))
            w.bind("<B1-Motion>",       lambda e, c=container: self._on_drag_move(e, c))
            w.bind("<ButtonRelease-1>", lambda e, c=container: self._on_drag_end(e, c))
            w.bind("<Button-3>",        lambda e, f=field: self._on_right_click_field(e, f))
            w.bind("<Double-Button-1>", lambda e, f=field: self._toggle_field_visible(f))

    # ═════════════════════════════════════════════
    # رندر دکمه‌ها
    # ═════════════════════════════════════════════
    def _render_all_buttons(self):
        for action in sorted(self.form_page.buttons, key=lambda a: a.order):
            if action.enabled:
                self._render_button(action, disabled=False)

    def _render_button(self, action: ActionButton, disabled: bool = False):
        meta = action_meta(action.action)
        icon = meta["icon"]

        bg_color = BTN_DISABLED_BG if disabled else BTN_BG
        text_color = "#666" if disabled else "#ffffff"

        w = action.width
        h = action.height + 14   # ⭐ برای handle

        container = tk.Frame(
            self.canvas,
            bg=bg_color,
            highlightthickness=2,
            highlightbackground=BTN_BORDER,
            highlightcolor=BTN_BORDER,
        )
        container.place(x=action.x, y=action.y, width=w, height=h)

        # ─── handle (نوار درگ) ───
        drag_bar = tk.Frame(
            container,
            bg="#3a3a3a" if not disabled else "#222",
            height=14,
            cursor="fleur",
        )
        drag_bar.pack(fill="x")
        drag_bar.pack_propagate(False)

        ctk.CTkLabel(
            drag_bar,
            text="⋮⋮",
            text_color="#888" if not disabled else "#444",
            font=ctk.CTkFont(size=10),
        ).pack()

        # ─── محتوا ───
        inner = ctk.CTkFrame(container, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        title = f"{icon} {action.label}"
        if disabled:
            title += "  🚫"

        ctk.CTkLabel(
            inner,
            text=title,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=text_color,
        ).pack(pady=(2, 0))

        ctk.CTkLabel(
            inner,
            text=action.method,
            fg_color=METHOD_COLORS.get(action.method, "#666") if not disabled else "#333",
            corner_radius=3,
            width=44,
            height=14,
            font=ctk.CTkFont(size=8, weight="bold"),
            text_color="white" if not disabled else "#666",
        ).pack(pady=(0, 2))

        # ─── ذخیره + رویدادها ───
        self._rendered_buttons[action.id] = container
        container._field_id = action.id
        container._kind = "button"
        container._offset = None

        targets = [container, drag_bar, inner] + list(inner.winfo_children()) + list(drag_bar.winfo_children())
        for w_ in targets:
            w_.bind("<Button-1>",        lambda e, c=container: self._on_drag_start(e, c))
            w_.bind("<B1-Motion>",       lambda e, c=container: self._on_drag_move(e, c))
            w_.bind("<ButtonRelease-1>", lambda e, c=container: self._on_drag_end(e, c))
            w_.bind("<Button-3>",        lambda e, a=action: self._on_right_click_button(e, a))
            w_.bind("<Double-Button-1>", lambda e, a=action: self._open_button_editor(a))

    # ═════════════════════════════════════════════
    # Drag
    # ═════════════════════════════════════════════
    def _on_drag_start(self, event, container):
        container._offset = (
            event.x_root - container.winfo_rootx(),
            event.y_root - container.winfo_rooty(),
        )
        self._select(container._field_id, container._kind)

    def _on_drag_move(self, event, container):
        if container._offset is None:
            return

        nx = event.x_root - self.canvas.winfo_rootx() - container._offset[0]
        ny = event.y_root - self.canvas.winfo_rooty() - container._offset[1]

        nx = (nx // GRID_SIZE) * GRID_SIZE
        ny = (ny // GRID_SIZE) * GRID_SIZE

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        w = container.winfo_width()
        h = container.winfo_height()

        if cw > 1:
            nx = max(0, min(nx, cw - w))
        if ch > 1:
            ny = max(0, min(ny, ch - h))

        container.place(x=nx, y=ny, width=w, height=h)

        if container._kind == "field":
            f = self.form_page.find_field(container._field_id)
            if f:
                f.x, f.y = nx, ny
        else:
            b = self.form_page.find_button(container._field_id)
            if b:
                b.x, b.y = nx, ny

    def _on_drag_end(self, event, container):
        container._offset = None

    # ═════════════════════════════════════════════
    # انتخاب
    # ═════════════════════════════════════════════
    def _select(self, item_id: str, kind: str):
        self._clear_selection()
        self._selected_id = item_id
        self._selected_kind = kind

        if kind == "field" and item_id in self._rendered_fields:
            self._rendered_fields[item_id].configure(highlightbackground=FIELD_SEL)
        elif kind == "button" and item_id in self._rendered_buttons:
            self._rendered_buttons[item_id].configure(highlightbackground=BTN_SEL)

    def _clear_selection(self):
        if self._selected_id:
            if self._selected_kind == "field" and self._selected_id in self._rendered_fields:
                self._rendered_fields[self._selected_id].configure(highlightbackground=FIELD_BORDER)
            elif self._selected_kind == "button" and self._selected_id in self._rendered_buttons:
                self._rendered_buttons[self._selected_id].configure(highlightbackground=BTN_BORDER)

        self._selected_id = None
        self._selected_kind = None

    def _on_canvas_click(self, event):
        if event.widget == self.canvas:
            self._clear_selection()

    # ═════════════════════════════════════════════
    def _toggle_field_visible(self, field: FieldElement):
        field.visible = not field.visible
        if field.id in self._rendered_fields:
            self._rendered_fields[field.id].destroy()
            del self._rendered_fields[field.id]
        self._render_field(field)

    # ═════════════════════════════════════════════
    def _open_button_editor(self, action: ActionButton):
        ButtonEditorDialog(
            self.winfo_toplevel(),
            self.form_page,
            action,
            on_save=lambda a: self.refresh_buttons(),
        )

    # ═════════════════════════════════════════════
    # راست‌کلیک
    # ═════════════════════════════════════════════
    def _on_right_click_field(self, event, field: FieldElement):
        menu = ctk.CTkToplevel(self)
        menu.geometry(f"+{event.x_root}+{event.y_root}")
        menu.overrideredirect(True)
        menu.attributes("-topmost", True)

        def close(): menu.destroy()

        vis_label = "🚫 مخفی کن" if field.visible else "👁 نمایش بده"
        ctk.CTkButton(
            menu, text=vis_label,
            fg_color="#444", hover_color="#555",
            width=200,
            command=lambda: (close(), self._toggle_field_visible(field)),
        ).pack(padx=4, pady=(4, 2))

        s_label = "🔍 حذف از جستجو" if field.searchable else "🔍 قابل جستجو کن"
        def toggle_search():
            field.searchable = not field.searchable
            close()
            if field.id in self._rendered_fields:
                self._rendered_fields[field.id].destroy()
                del self._rendered_fields[field.id]
            self._render_field(field)

        ctk.CTkButton(
            menu, text=s_label,
            fg_color="#444", hover_color="#555",
            width=200,
            command=toggle_search,
        ).pack(padx=4, pady=2)

        ctk.CTkButton(
            menu, text=f"🗑  حذف «{field.label}»",
            fg_color="#c0392b", hover_color="#a93226",
            width=200,
            command=lambda: (close(), self._remove_field(field.id)),
        ).pack(padx=4, pady=(2, 4))

        menu.after(4000, lambda: menu.winfo_exists() and menu.destroy())

    def _on_right_click_button(self, event, action: ActionButton):
        menu = ctk.CTkToplevel(self)
        menu.geometry(f"+{event.x_root}+{event.y_root}")
        menu.overrideredirect(True)
        menu.attributes("-topmost", True)

        def close(): menu.destroy()

        ctk.CTkButton(
            menu, text="✏  ویرایش دکمه",
            fg_color="#0d6efd", hover_color="#0b5ed7",
            width=200,
            command=lambda: (close(), self._open_button_editor(action)),
        ).pack(padx=4, pady=(4, 2))

        t_label = "🚫 غیرفعال کن" if action.enabled else "✅ فعال کن"
        def toggle_enabled():
            action.enabled = not action.enabled
            close()
            self.refresh_buttons()

        ctk.CTkButton(
            menu, text=t_label,
            fg_color="#444", hover_color="#555",
            width=200,
            command=toggle_enabled,
        ).pack(padx=4, pady=2)

        ctk.CTkButton(
            menu, text=f"🗑  حذف «{action.label}»",
            fg_color="#c0392b", hover_color="#a93226",
            width=200,
            command=lambda: (close(), self._remove_button(action.id)),
        ).pack(padx=4, pady=(2, 4))

        menu.after(4000, lambda: menu.winfo_exists() and menu.destroy())

    # ═════════════════════════════════════════════
    # حذف
    # ═════════════════════════════════════════════
    def _remove_field(self, field_id: str):
        if field_id in self._rendered_fields:
            self._rendered_fields[field_id].destroy()
            del self._rendered_fields[field_id]

        self.form_page.remove_field(field_id)
        if self._selected_id == field_id:
            self._selected_id = None
        self._update_count()

        if self.on_fields_change:
            self.on_fields_change()

    def _remove_button(self, btn_id: str):
        if btn_id in self._rendered_buttons:
            self._rendered_buttons[btn_id].destroy()
            del self._rendered_buttons[btn_id]

        self.form_page.remove_button(btn_id)
        self.form_page.reorder_buttons()
        if self._selected_id == btn_id:
            self._selected_id = None
        self._update_count()

    # ═════════════════════════════════════════════
    # تغییر فرم / پاکسازی
    # ═════════════════════════════════════════════
    def set_form(self, form_page):
        self.clear()
        self.form_page = form_page
        self.title_lbl.configure(text=f"🎨 Canvas — {form_page.name}")
        self._render_all_fields()
        self._render_all_buttons()
        self._update_count()

    def clear(self):
        for w in list(self._rendered_fields.values()):
            w.destroy()
        for w in list(self._rendered_buttons.values()):
            w.destroy()
        self._rendered_fields.clear()
        self._rendered_buttons.clear()
        self._selected_id = None
        self._selected_kind = None

    def _update_count(self):
        nf = len(self.form_page.fields)
        nb_total = len(self.form_page.buttons)
        nb_enabled = sum(1 for b in self.form_page.buttons if b.enabled)
        self.count_lbl.configure(
            text=f"{nf} فیلد  •  {nb_enabled}/{nb_total} دکمه فعال"
        )

    # ═════════════════════════════════════════════
    # کمکی
    # ═════════════════════════════════════════════
    @staticmethod
    def _icon_for(widget_type: str) -> str:
        return {
            "number":    "🔢",
            "textfield": "🔤",
            "textarea":  "📝",
            "date":      "📅",
            "datetime":  "🕐",
            "time":      "⏱",
            "checkbox":  "☑️",
            "dropdown":  "🔽",
        }.get(widget_type, "🔹")

    @staticmethod
    def _placeholder_for(widget_type: str) -> str:
        return {
            "number":    "عدد وارد کنید",
            "textfield": "متن وارد کنید",
            "textarea":  "متن طولانی...",
            "date":      "YYYY-MM-DD",
            "datetime":  "YYYY-MM-DD HH:MM",
            "time":      "HH:MM",
            "checkbox":  "true / false",
            "dropdown":  "انتخاب کنید",
        }.get(widget_type, "")