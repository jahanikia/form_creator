# src/services/default_schema.py
"""
جداول پیش‌فرض + گروه‌های پیش‌فرض
─────────────────────────────────
12 جدول:
  auth: users, user_profiles, roles, permissions, user_roles,
        role_permissions, sessions, password_resets, otp_codes,
        login_attempts, jwt_blacklist
  logs: user_activities
"""

from src.models.custom_schema import CustomTable, CustomColumn, TableGroup


# ═══════════════════════════════════════════════════════════
# توابع کمکی — همه با BIGINT UNSIGNED برای PK/FK
# ═══════════════════════════════════════════════════════════
def pk_id() -> CustomColumn:
    return CustomColumn(
        name="id", fa_name="شناسه",
        data_type="BIGINT UNSIGNED",   # ⭐ UNSIGNED
        allow_null=False,
        is_primary=True,
        is_auto_increment=True,
        is_unique=True,
        comment="کلید اصلی",
    )


def fk(name: str, fa: str, to_table: str,
       nullable: bool = False) -> CustomColumn:
    return CustomColumn(
        name=name, fa_name=fa,
        data_type="BIGINT UNSIGNED",   # ⭐ UNSIGNED (هم‌نوع با PK)
        allow_null=nullable,
        is_searchable=True,
        comment=f"FK → {to_table}",
    )


def vc(name: str, fa: str, size: int = 150,
       nullable: bool = False, default: str = "",
       unique: bool = False, searchable: bool = True) -> CustomColumn:
    return CustomColumn(
        name=name, fa_name=fa,
        data_type=f"VARCHAR({size})",
        allow_null=nullable,
        default_value=default,
        is_unique=unique,
        is_searchable=searchable,
    )


def txt(name: str, fa: str, nullable: bool = True,
        default: str = "NULL") -> CustomColumn:
    return CustomColumn(
        name=name, fa_name=fa,
        data_type="TEXT",
        allow_null=nullable,
        default_value=default,
        is_searchable=False,
    )


def ts_created() -> CustomColumn:
    return CustomColumn(
        name="created_at", fa_name="زمان ایجاد",
        data_type="TIMESTAMP",
        allow_null=False,
        default_value="CURRENT_TIMESTAMP",
        is_searchable=False,
    )


def ts_updated() -> CustomColumn:
    return CustomColumn(
        name="updated_at", fa_name="زمان ویرایش",
        data_type="TIMESTAMP",
        allow_null=False,
        default_value="CURRENT_TIMESTAMP",
        comment="ON UPDATE CURRENT_TIMESTAMP",
        is_searchable=False,
    )


def ts_nullable(name: str, fa: str) -> CustomColumn:
    """⭐ آپدیت: بدون DEFAULT NULL — فقط allow_null"""
    return CustomColumn(
        name=name, fa_name=fa,
        data_type="TIMESTAMP",
        allow_null=True,
        default_value="",   # ⭐ خالی (نه "NULL")
        is_searchable=False,
    )


def bool_col(name: str, fa: str, default: str = "1") -> CustomColumn:
    return CustomColumn(
        name=name, fa_name=fa,
        data_type="BOOLEAN",
        allow_null=False,
        default_value=default,
        is_searchable=True,
    )


def int_col(name: str, fa: str, default: str = "0",
            nullable: bool = False) -> CustomColumn:
    return CustomColumn(
        name=name, fa_name=fa,
        data_type="INT",
        allow_null=nullable,
        default_value=default,
        is_searchable=True,
    )


def ip_col(name: str = "ip_address", fa: str = "آدرس IP") -> CustomColumn:
    return CustomColumn(
        name=name, fa_name=fa,
        data_type="VARCHAR(45)",
        allow_null=True,
        default_value="",
        is_searchable=False,
    )


# ═══════════════════════════════════════════════════════════
# گروه‌های پیش‌فرض
# ═══════════════════════════════════════════════════════════
def get_default_groups(project_id: int) -> list[TableGroup]:
    return [
        TableGroup(
            project_id=project_id,
            name="auth", fa_name="احراز هویت",
            icon="🔐", color="#0d6efd",
            order_index=1, is_default=True,
        ),
        TableGroup(
            project_id=project_id,
            name="logs", fa_name="لاگ‌ها",
            icon="📊", color="#fd7e14",
            order_index=2, is_default=True,
        ),
        TableGroup(
            project_id=project_id,
            name="content", fa_name="محتوا",
            icon="📝", color="#198754",
            order_index=3, is_default=True,
        ),
        TableGroup(
            project_id=project_id,
            name="custom", fa_name="سفارشی",
            icon="📁", color="#6f42c1",
            order_index=4, is_default=True,
        ),
    ]


def table_default_group(table_name: str) -> str:
    auth_tables = {
        "users", "user_profiles", "roles", "permissions", "user_roles",
        "role_permissions", "sessions", "password_resets", "otp_codes",
        "login_attempts", "jwt_blacklist",
    }
    logs_tables = {"user_activities"}
    if table_name in auth_tables:
        return "auth"
    if table_name in logs_tables:
        return "logs"
    return "custom"


# ═══════════════════════════════════════════════════════════
# جداول پیش‌فرض
# ═══════════════════════════════════════════════════════════
def get_default_tables(project_id: int) -> list[CustomTable]:
    tables = []

    # ═══ 1. users ═══
    users = CustomTable(
        project_id=project_id,
        name="users", fa_name="کاربران",
        description="جدول اصلی کاربران",
        is_default=True, order_index=1,
    )
    users.columns = [
        pk_id(),
        vc("first_name", "نام", 100),
        vc("last_name", "نام خانوادگی", 100),
        vc("user_name", "نام کاربری", 50, unique=True),
        vc("email", "ایمیل", 150, unique=True),
        vc("password", "رمز عبور (hash)", 255, searchable=False),
        vc("mobile", "موبایل", 20, nullable=True, default=""),
        bool_col("is_active", "فعال", default="1"),
        bool_col("is_verified", "تأیید شده", default="0"),
        ts_nullable("last_login_at", "آخرین ورود"),
        ts_created(),
        ts_updated(),
    ]
    tables.append(users)

    # ═══ 2. user_profiles ═══
    profiles = CustomTable(
        project_id=project_id,
        name="user_profiles", fa_name="پروفایل کاربران",
        description="اطلاعات تکمیلی پروفایل (یک‌به‌یک با users)",
        is_default=True, order_index=2,
    )
    profiles.columns = [
        pk_id(),
        fk("user_id", "کاربر", "users"),
        vc("bio", "بیوگرافی", 500, nullable=True, default="", searchable=True),
        txt("address", "آدرس", nullable=True),
        vc("city", "شهر", 100, nullable=True, default=""),
        vc("country", "کشور", 100, nullable=True, default=""),
        vc("postal_code", "کد پستی", 20, nullable=True, default=""),
        vc("image_url", "آدرس تصویر", 500, nullable=True, default="",
           searchable=False),
        vc("website", "وب‌سایت", 255, nullable=True, default="",
           searchable=False),
        vc("birth_date", "تاریخ تولد", 20, nullable=True, default=""),
        vc("gender", "جنسیت", 20, nullable=True, default=""),
        ts_created(),
        ts_updated(),
    ]
    # user_id یکتا (یک‌به‌یک)
    profiles.columns[1].is_unique = True
    tables.append(profiles)

    # ═══ 3. roles ═══
    roles = CustomTable(
        project_id=project_id,
        name="roles", fa_name="نقش‌ها",
        description="نقش‌های کاربری (RBAC)",
        is_default=True, order_index=3,
    )
    roles.columns = [
        pk_id(),
        vc("name", "نام نقش", 50, unique=True),
        vc("display_name", "نام نمایشی", 100, nullable=True, default=""),
        txt("description", "توضیحات"),
        bool_col("is_system", "سیستمی", default="0"),
        ts_created(),
        ts_updated(),
    ]
    tables.append(roles)

    # ═══ 4. permissions ═══
    perms = CustomTable(
        project_id=project_id,
        name="permissions", fa_name="مجوزها",
        description="مجوزهای ریز دسترسی",
        is_default=True, order_index=4,
    )
    perms.columns = [
        pk_id(),
        vc("name", "نام مجوز", 100, unique=True),
        vc("display_name", "نام نمایشی", 150, nullable=True, default=""),
        vc("resource", "منبع", 100, nullable=True, default=""),
        vc("action", "عملیات", 50, nullable=True, default=""),
        txt("description", "توضیحات"),
        ts_created(),
    ]
    tables.append(perms)

    # ═══ 5. user_roles ═══
    ur = CustomTable(
        project_id=project_id,
        name="user_roles", fa_name="نقش‌های کاربران",
        description="جدول واسط بین کاربران و نقش‌ها",
        is_default=True, order_index=5,
    )
    ur.columns = [
        pk_id(),
        fk("user_id", "کاربر", "users"),
        fk("role_id", "نقش", "roles"),
        ts_created(),
    ]
    tables.append(ur)

    # ═══ 6. role_permissions ═══
    rp = CustomTable(
        project_id=project_id,
        name="role_permissions", fa_name="مجوزهای نقش‌ها",
        description="جدول واسط بین نقش‌ها و مجوزها",
        is_default=True, order_index=6,
    )
    rp.columns = [
        pk_id(),
        fk("role_id", "نقش", "roles"),
        fk("permission_id", "مجوز", "permissions"),
        ts_created(),
    ]
    tables.append(rp)

    # ═══ 7. sessions ═══
    sessions = CustomTable(
        project_id=project_id,
        name="sessions", fa_name="نشست‌ها",
        description="نشست‌های فعال کاربران",
        is_default=True, order_index=7,
    )
    sessions.columns = [
        pk_id(),
        fk("user_id", "کاربر", "users"),
        vc("token", "توکن", 255, unique=True, searchable=False),
        ip_col(),
        vc("user_agent", "User Agent", 255, nullable=True, default="",
           searchable=False),
        ts_nullable("expires_at", "زمان انقضا"),
        ts_created(),
    ]
    tables.append(sessions)

    # ═══ 8. password_resets ═══
    pr = CustomTable(
        project_id=project_id,
        name="password_resets", fa_name="بازیابی رمز",
        description="درخواست‌های بازیابی رمز عبور",
        is_default=True, order_index=8,
    )
    pr.columns = [
        pk_id(),
        vc("email", "ایمیل", 150, searchable=True),
        vc("token", "توکن", 255, unique=True, searchable=False),
        ts_nullable("expires_at", "زمان انقضا"),
        ts_nullable("used_at", "زمان استفاده"),
        ts_created(),
    ]
    tables.append(pr)

    # ═══ 9. otp_codes ═══
    otp = CustomTable(
        project_id=project_id,
        name="otp_codes", fa_name="کدهای یکبار مصرف",
        description="کدهای OTP برای ورود/تأیید",
        is_default=True, order_index=9,
    )
    otp.columns = [
        pk_id(),
        vc("identifier", "شناسه (ایمیل/موبایل)", 100, searchable=True),
        vc("code", "کد", 10, searchable=False),
        vc("purpose", "هدف", 50, default="login"),
        int_col("attempts", "تلاش‌های ناموفق", default="0"),
        int_col("max_attempts", "حداکثر تلاش", default="5"),
        ts_nullable("expires_at", "زمان انقضا"),
        ts_nullable("used_at", "زمان استفاده"),
        ip_col(),
        ts_created(),
    ]
    tables.append(otp)

    # ═══ 10. login_attempts ═══
    la = CustomTable(
        project_id=project_id,
        name="login_attempts", fa_name="تلاش‌های ورود",
        description="ثبت تلاش‌های ورود برای Rate Limiting",
        is_default=True, order_index=10,
    )
    la.columns = [
        pk_id(),
        vc("identifier", "شناسه ورود (username/email/mobile)", 100,
           searchable=True),
        CustomColumn(
            name="ip_address", fa_name="آدرس IP",
            data_type="VARCHAR(45)",
            allow_null=False,
            is_searchable=True,
        ),
        txt("user_agent", "مرورگر", nullable=True),
        bool_col("success", "موفق", default="0"),
        vc("failure_reason", "دلیل شکست", 255, nullable=True, default=""),
        CustomColumn(
            name="attempted_at", fa_name="زمان تلاش",
            data_type="TIMESTAMP",
            allow_null=False,
            default_value="CURRENT_TIMESTAMP",
            is_searchable=False,
        ),
    ]
    tables.append(la)

    # ═══ 11. user_activities ═══
    ua = CustomTable(
        project_id=project_id,
        name="user_activities", fa_name="فعالیت‌های کاربران",
        description="لاگ فعالیت‌های کاربران",
        is_default=True, order_index=11,
    )
    ua.columns = [
        pk_id(),
        fk("user_id", "کاربر", "users", nullable=True),   # ⭐ می‌تونه NULL باشه
        vc("action", "عملیات", 100, searchable=True),
        vc("resource", "منبع", 100, nullable=True, default="", searchable=True),
        txt("details", "جزئیات"),
        ip_col(),
        vc("user_agent", "User Agent", 255, nullable=True, default="",
           searchable=False),
        ts_created(),
    ]
    tables.append(ua)

    # ═══ 12. jwt_blacklist ═══
    jwt = CustomTable(
        project_id=project_id,
        name="jwt_blacklist", fa_name="JWT Blacklist",
        description="توکن‌های JWT باطل‌شده",
        is_default=True, order_index=12,
    )
    jwt.columns = [
        pk_id(),
        vc("token", "توکن", 500, unique=True, searchable=False),
        fk("user_id", "کاربر", "users", nullable=True),
        ts_nullable("expires_at", "زمان انقضا"),
        ts_created(),
    ]
    tables.append(jwt)

    return tables


DEFAULT_TABLE_NAMES = {
    "users", "user_profiles", "roles", "permissions", "user_roles",
    "role_permissions", "sessions", "password_resets", "otp_codes",
    "login_attempts", "user_activities", "jwt_blacklist",
}