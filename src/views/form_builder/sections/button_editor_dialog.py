# src/views/form_builder/sections/button_editor_dialog.py
"""
مودال ویرایش دکمه
─────────────────────────────────
• تغییر label / endpoint / method / action
• انتخاب فیلدهای payload (checkbox)
• فعال/غیرفعال کردن دکمه
• توضیحات
"""

import customtkinter as ctk
from tkinter import messagebox

from src.models.form_schema import (
    FormPage, ActionButton,
    ACTION_META, action_meta,
)
from src.services.payload_resolver import suggest_payload


BG_DIALOG   = "#1e1e1e"
BG_SECTION  = "#252525"
BG_ROW      = "#2e2e2e"
FG_PRIMARY  = "#0d6efd"
FG_SUCCESS  = "#198754"
FG_DANGER   = "#c0392b"
FG_NEUTRAL  = "#444"

METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
ACTIONS = ["create", "read", "update", "delete", "search", "custom"]


class ButtonEditorDialog(ctk.CTkToplevel):
    """مودال ویرایش دکمه"""

    def __init__(self, master, form_page: FormPage, action: ActionButton,
                 on_save=None):
        super().__init__(master)
        self.form_page = form_page
        self.action = action
        self.on_save = on_save

        # ═══ پنجره ═══
        self.title(f"✏️ ویرایش دکمه — {action.label}")
        self.geometry("620x720")
        self.minsize(560, 600)
        self.configure(fg_color=BG_DIALOG)

        # مودال واقعی
        self.transient(master)
        self.grab_set()

        # ═══ وضعیت محلی (کپی از action) ═══
        self._label_var    = ctk.StringVar(value=action.label)
        self._method_var   = ctk.StringVar(value=action.method)
        self._action_var   = ctk.StringVar(value=action.action)
        self._endpoint_var = ctk.StringVar(value=action.endpoint)
        self._enabled_var  = ctk.BooleanVar(value=action.enabled)
        self._desc_var     = ctk.StringVar(value=action.description or "")

        # payload: set از column هایی که تیک خوردن
        suggested = form_page.suggested_payload_fields(action)
        self._payload_set = set(suggested)
        self._payload_vars: dict[str, ctk.BooleanVar] = {}

        # ═══ UI ═══
        self._build()

        # کلید Escape برای بستن
        self.bind("<Escape>", lambda e: self.destroy())

        # فوکوس
        self.after(50, self.focus_force)

    # ═════════════════════════════════════════════
    def _build(self):
        # ─── هدر ───
        header = ctk.CTkFrame(self, fg_color=BG_SECTION, height=60, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text=f"⚙️  ویرایش دکمه",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left", padx=16)

        ctk.CTkLabel(
            header,
            text=f"({self.action.id})",
            text_color="#888",
            font=ctk.CTkFont(size=10),
        ).pack(side="left")

        # ─── بدنه قابل اسکرول ───
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=14, pady=12)

        # ═══ بخش ۱: اطلاعات پایه ═══
        self._section(body, "🔖 اطلاعات پایه")
        self._field_row(body, "برچسب (Label):", self._label_var)
        self._field_row(body, "توضیحات (Description):", self._desc_var)

        # ═══ بخش ۲: اکشن و HTTP ═══
        self._section(body, "🌐 اکشن و HTTP")

        # action dropdown
        action_row = ctk.CTkFrame(body, fg_color=BG_ROW, corner_radius=6)
        action_row.pack(fill="x", pady=3)

        ctk.CTkLabel(
            action_row,
            text="نوع اکشن:",
            width=140,
            anchor="w",
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(10, 6), pady=8)

        self._action_menu = ctk.CTkOptionMenu(
            action_row,
            values=ACTIONS,
            variable=self._action_var,
            command=self._on_action_change,
            width=200,
        )
        self._action_menu.pack(side="left", pady=8, padx=4)

        # method dropdown
        method_row = ctk.CTkFrame(body, fg_color=BG_ROW, corner_radius=6)
        method_row.pack(fill="x", pady=3)

        ctk.CTkLabel(
            method_row,
            text="HTTP Method:",
            width=140,
            anchor="w",
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(10, 6), pady=8)

        self._method_menu = ctk.CTkOptionMenu(
            method_row,
            values=METHODS,
            variable=self._method_var,
            width=200,
        )
        self._method_menu.pack(side="left", pady=8, padx=4)

        # endpoint
        self._field_row(body, "Endpoint:", self._endpoint_var,
                        hint="مثال: /api/users  یا  /api/users/{id}")

        # ═══ بخش ۳: payload ═══
        self._section(body, "📦 فیلدهای payload")

        # دکمه‌های کمکی
        helper_row = ctk.CTkFrame(body, fg_color="transparent")
        helper_row.pack(fill="x", pady=(0, 6))

        ctk.CTkButton(
            helper_row,
            text="🤖 پیشنهاد خودکار",
            fg_color=FG_PRIMARY,
            hover_color="#0b5ed7",
            width=140,
            height=28,
            font=ctk.CTkFont(size=11),
            command=self._apply_suggestion,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            helper_row,
            text="✅ انتخاب همه",
            fg_color=FG_NEUTRAL,
            hover_color="#555",
            width=110,
            height=28,
            font=ctk.CTkFont(size=11),
            command=lambda: self._toggle_all(True),
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            helper_row,
            text="❌ حذف همه",
            fg_color=FG_NEUTRAL,
            hover_color="#555",
            width=100,
            height=28,
            font=ctk.CTkFont(size=11),
            command=lambda: self._toggle_all(False),
        ).pack(side="left", padx=3)

        # توضیح استراتژی
        self._strategy_lbl = ctk.CTkLabel(
            body,
            text="",
            text_color="#888",
            font=ctk.CTkFont(size=10),
            anchor="w",
            justify="left",
        )
        self._strategy_lbl.pack(fill="x", padx=4, pady=(0, 6))

        # لیست فیلدها
        self._payload_frame = ctk.CTkFrame(body, fg_color="#1a1a1a", corner_radius=6)
        self._payload_frame.pack(fill="x", pady=4)

        self._build_payload_list()

        # ═══ بخش ۴: وضعیت ═══
        self._section(body, "⚙️ وضعیت")

        enabled_row = ctk.CTkFrame(body, fg_color=BG_ROW, corner_radius=6)
        enabled_row.pack(fill="x", pady=3)

        ctk.CTkCheckBox(
            enabled_row,
            text="دکمه فعال باشد (روی فرم نمایش داده شود)",
            variable=self._enabled_var,
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=12, pady=10)

        # ═══ نوار پایین (دکمه‌ها) ═══
        footer = ctk.CTkFrame(self, fg_color=BG_SECTION, height=64, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        ctk.CTkButton(
            footer,
            text="💾  ذخیره تغییرات",
            fg_color=FG_SUCCESS,
            hover_color="#146c43",
            width=160,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save,
        ).pack(side="right", padx=(6, 14), pady=13)

        ctk.CTkButton(
            footer,
            text="انصراف",
            fg_color=FG_NEUTRAL,
            hover_color="#555",
            width=100,
            height=38,
            command=self.destroy,
        ).pack(side="right", padx=6, pady=13)

    # ═════════════════════════════════════════════
    # اجزای UI
    # ═════════════════════════════════════════════
    def _section(self, parent, title: str):
        lbl = ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9ecbff",
            anchor="w",
        )
        lbl.pack(fill="x", pady=(12, 4), padx=2)

    def _field_row(self, parent, label: str, var, hint: str = ""):
        row = ctk.CTkFrame(parent, fg_color=BG_ROW, corner_radius=6)
        row.pack(fill="x", pady=3)

        ctk.CTkLabel(
            row,
            text=label,
            width=140,
            anchor="w",
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(10, 6), pady=8)

        entry = ctk.CTkEntry(row, textvariable=var, height=30)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=8)

        if hint:
            ctk.CTkLabel(
                parent,
                text=hint,
                text_color="#666",
                font=ctk.CTkFont(size=9),
                anchor="w",
            ).pack(fill="x", padx=8, pady=(0, 2))

    # ═════════════════════════════════════════════
    # لیست payload
    # ═════════════════════════════════════════════
    def _build_payload_list(self):
        for w in self._payload_frame.winfo_children():
            w.destroy()
        self._payload_vars.clear()

        if not self.form_page.fields:
            ctk.CTkLabel(
                self._payload_frame,
                text="هیچ فیلدی روی فرم نیست",
                text_color="#666",
                font=ctk.CTkFont(size=11),
            ).pack(pady=20)
            return

        for field in self.form_page.fields:
            row = ctk.CTkFrame(self._payload_frame, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=2)

            var = ctk.BooleanVar(value=field.column in self._payload_set)
            self._payload_vars[field.column] = var

            # چک‌باکس اصلی
            cb = ctk.CTkCheckBox(
                row,
                text="",
                variable=var,
                width=20,
                checkbox_width=18,
                checkbox_height=18,
            )
            cb.pack(side="left", padx=(0, 6))

            # نام ستون
            ctk.CTkLabel(
                row,
                text=field.column,
                width=130,
                anchor="w",
                font=ctk.CTkFont(size=12),
            ).pack(side="left")

            # نوع
            ctk.CTkLabel(
                row,
                text=field.widget_type,
                width=80,
                anchor="w",
                text_color="#888",
                font=ctk.CTkFont(size=10),
            ).pack(side="left")

            # badge auto
            if field.auto_fill:
                ctk.CTkLabel(
                    row,
                    text=f"⚡ {field.auto_fill}",
                    text_color="#7bd88f",
                    font=ctk.CTkFont(size=10),
                ).pack(side="left", padx=4)

            # badge searchable
            if field.searchable:
                ctk.CTkLabel(
                    row,
                    text="🔍",
                    font=ctk.CTkFont(size=10),
                ).pack(side="left", padx=4)

            # badge visible
            if not field.visible:
                ctk.CTkLabel(
                    row,
                    text="🚫 مخفی",
                    text_color="#c97a7a",
                    font=ctk.CTkFont(size=10),
                ).pack(side="left", padx=4)

    # ═════════════════════════════════════════════
    # رویدادها
    # ═════════════════════════════════════════════
    def _on_action_change(self, new_action: str):
        """وقتی کاربر نوع action رو عوض کرد، endpoint و method پیشنهادی رو بذار"""
        meta = action_meta(new_action)
        self._method_var.set(meta["method"])

        tpl = meta["endpoint_tpl"]
        endpoint = tpl.replace("{table}", self.form_page.table)
        # اگه هنوز {id} توش هست، دست نمی‌زنیم
        endpoint = endpoint.replace("{id}", "{id}")
        self._endpoint_var.set(endpoint)

        # پیشنهاد جدید
        self._apply_suggestion()

    def _apply_suggestion(self):
        """اعمال پیشنهاد خودکار"""
        action_key = self._action_var.get()

        # یه action موقت بساز برای پیشنهاد
        temp = ActionButton(
            id=self.action.id,
            label=self._label_var.get(),
            action=action_key,
            method=self._method_var.get(),
            endpoint=self._endpoint_var.get(),
            payload_fields=[],   # خالی → پیشنهاد خودکار
        )
        sug = suggest_payload(self.form_page, temp)

        # اعمال روی UI
        for col, var in self._payload_vars.items():
            var.set(col in sug.fields)

        self._payload_set = set(sug.fields)
        self._strategy_lbl.configure(
            text=f"🤖 پیشنهاد: {sug.reason}  |  {len(sug.fields)} فیلد"
        )

    def _toggle_all(self, value: bool):
        for var in self._payload_vars.values():
            var.set(value)

    # ═════════════════════════════════════════════
    # ذخیره
    # ═════════════════════════════════════════════
    def _save(self):
        label = self._label_var.get().strip()
        endpoint = self._endpoint_var.get().strip()
        method = self._method_var.get()
        action_key = self._action_var.get()

        # اعتبارسنجی
        if not label:
            messagebox.showwarning("خطا", "برچسب نمی‌تونه خالی باشه", parent=self)
            return
        if not endpoint:
            messagebox.showwarning("خطا", "Endpoint نمی‌تونه خالی باشه", parent=self)
            return
        if not endpoint.startswith("/"):
            messagebox.showwarning("خطا", "Endpoint باید با / شروع بشه", parent=self)
            return

        # فیلدهای انتخابی
        selected = [col for col, var in self._payload_vars.items() if var.get()]

        # ⭐ اعمال روی action واقعی
        self.action.label = label
        self.action.endpoint = endpoint
        self.action.method = method
        self.action.action = action_key
        self.action.enabled = self._enabled_var.get()
        self.action.description = self._desc_var.get().strip()

        # اگه فیلدها با پیشنهاد خودکار یکسانن، خالی بذار (یعنی auto)
        temp = ActionButton(
            id=self.action.id, label=label, action=action_key,
            method=method, endpoint=endpoint, payload_fields=[],
        )
        sug = suggest_payload(self.form_page, temp)
        if set(selected) == set(sug.fields):
            self.action.payload_fields = []     # auto
        else:
            self.action.payload_fields = selected

        # callback
        if self.on_save:
            self.on_save(self.action)

        self.destroy()