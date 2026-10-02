# src/views/main_view/sections/status_bar.py
"""
StatusBarSection — نوار وضعیت پایین
"""

import customtkinter as ctk
from datetime import datetime


BG_STATUS = "#141414"


class StatusBarSection(ctk.CTkFrame):
    """نوار وضعیت"""

    def __init__(self, master):
        super().__init__(master, fg_color=BG_STATUS, height=30, corner_radius=0)
        self.pack_propagate(False)

        # ─── چپ: وضعیت ───
        self.status_lbl = ctk.CTkLabel(
            self,
            text="آماده",
            text_color="#aaa",
            font=ctk.CTkFont(size=11),
        )
        self.status_lbl.pack(side="left", padx=14)

        # ─── راست: آخرین به‌روزرسانی ───
        self.time_lbl = ctk.CTkLabel(
            self,
            text="",
            text_color="#666",
            font=ctk.CTkFont(size=10),
        )
        self.time_lbl.pack(side="right", padx=14)

        self.update_time()

    # ═════════════════════════════════════════════
    def set_status(self, text: str):
        self.status_lbl.configure(text=text)
        self.update_time()

    def update_time(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.time_lbl.configure(text=f"آخرین به‌روزرسانی: {now}")