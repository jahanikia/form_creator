# src/services/payload_resolver.py
"""
Payload Resolver
─────────────────────────────────
مسئول انتخاب خودکار فیلدهای ورودی برای هر دکمه.
UI می‌تونه از این استفاده کنه تا به کاربر پیشنهاد بده.
"""

from typing import List
from src.models.form_schema import FormPage, ActionButton, action_meta


class PayloadSuggestion:
    """نتیجه‌ی پیشنهاد payload"""

    def __init__(self, fields: List[str], strategy: str, reason: str):
        self.fields = fields
        self.strategy = strategy
        self.reason = reason

    def __repr__(self):
        return f"<PayloadSuggestion fields={self.fields} strategy={self.strategy}>"


def suggest_payload(form: FormPage, action: ActionButton) -> PayloadSuggestion:
    """
    پیشنهاد خودکار payload برای یک دکمه.

    اولویت:
      1. اگه action.payload_fields دستی ست شده → از همون استفاده کن
      2. اگه نه → بر اساس استراتژی action
    """
    # حالت ۱: کاربر قبلاً تنظیم کرده
    if action.payload_fields:
        return PayloadSuggestion(
            fields=list(action.payload_fields),
            strategy="manual",
            reason="کاربر دستی انتخاب کرده",
        )

    # حالت ۲: استراتژی خودکار
    meta = action_meta(action.action)
    strategy = meta.get("default_payload", "none")
    fields = form._resolve_payload_fields(strategy)

    reason_map = {
        "none":              "این action ورودی نمی‌خواد",
        "pk_only":           "فقط کلید اصلی",
        "all_visible":       "همه‌ی فیلدهای قابل‌مشاهده",
        "visible_no_pk_auto":"فیلدهای قابل‌مشاهده، بدون PK و فیلدهای خودکار",
        "searchable_only":   "فقط فیلدهای قابل‌جستجو",
    }

    return PayloadSuggestion(
        fields=fields,
        strategy=strategy,
        reason=reason_map.get(strategy, ""),
    )