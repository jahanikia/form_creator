# src/utils/window_utils.py
"""
ابزارهای کار با پنجره
─────────────────────────────────
"""


class WindowUtils:
    """کمکی برای مدیریت پنجره"""

    @staticmethod
    def get_screen_size(widget) -> tuple[int, int]:
        """اندازه‌ی صفحه‌نمایش"""
        return widget.winfo_screenwidth(), widget.winfo_screenheight()

    @staticmethod
    def calculate_size(widget, desired_width: int = 1440,
                       desired_height: int = 860,
                       ratio: float = 0.9,
                       min_width: int = 1000,
                       min_height: int = 650) -> tuple[int, int]:
        """
        محاسبه‌ی اندازه‌ی مناسب پنجره بر اساس صفحه‌نمایش

        Args:
            desired_width: عرض دلخواه
            desired_height: ارتفاع دلخواه
            ratio: نسبت از صفحه‌نمایش (0.9 = 90%)
            min_width: حداقل عرض
            min_height: حداقل ارتفاع
        """
        sw, sh = WindowUtils.get_screen_size(widget)

        w = min(desired_width, int(sw * ratio))
        h = min(desired_height, int(sh * ratio))

        w = max(w, min_width)
        h = max(h, min_height)

        return w, h

    @staticmethod
    def center_window(widget, width: int, height: int):
        """وسط‌چین کردن پنجره روی صفحه"""
        sw, sh = WindowUtils.get_screen_size(widget)
        x = (sw - width) // 2
        y = (sh - height) // 2
        widget.geometry(f"{width}x{height}+{x}+{y}")