# src/services/db_connector.py
"""
DBConnector — اتصال به MySQL
"""

import re
from typing import Optional
import mysql.connector
from mysql.connector import Error as MySQLError


# ⭐ Collation پیش‌فرض
DEFAULT_COLLATION = "utf8mb4_persian_ci"
DEFAULT_CHARSET = "utf8mb4"


class DBConnector:
    """کلاینت MySQL"""

    def __init__(self, host: str = "localhost", port: int = 3306,
                 user: str = "root", password: str = "",
                 database: str = ""):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self._conn = None

    # ═════════════════════════════════════════════
    def connect(self, create_db_if_missing: bool = False) -> tuple[bool, str]:
        try:
            if self.database and create_db_if_missing:
                ok, msg = self._ensure_database_exists()
                if not ok:
                    return False, msg

            self._conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database or None,
                charset=DEFAULT_CHARSET,
                collation=DEFAULT_COLLATION,
                autocommit=False,
            )
            return True, "اتصال موفق"

        except MySQLError as e:
            return False, f"خطای MySQL: {e}"
        except Exception as e:
            return False, f"خطای غیرمنتظره: {e}"

    def _ensure_database_exists(self) -> tuple[bool, str]:
        try:
            conn = mysql.connector.connect(
                host=self.host, port=self.port,
                user=self.user, password=self.password,
                charset=DEFAULT_CHARSET,
            )
            cursor = conn.cursor()
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{self.database}` "
                f"CHARACTER SET {DEFAULT_CHARSET} "
                f"COLLATE {DEFAULT_COLLATION}"
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True, "دیتابیس آماده است"
        except MySQLError as e:
            return False, f"خطا در ساخت دیتابیس: {e}"

    def disconnect(self):
        if self._conn and self._conn.is_connected():
            try:
                self._conn.close()
            except Exception:
                pass
        self._conn = None

    def is_connected(self) -> bool:
        return self._conn is not None and self._conn.is_connected()

    # ═════════════════════════════════════════════
    def execute_sql(self, sql: str, split: bool = True) -> tuple[bool, str]:
        if not self.is_connected():
            return False, "اتصال برقرار نیست"

        try:
            cursor = self._conn.cursor()

            if split:
                statements = self._split_sql(sql)
            else:
                statements = [sql]

            executed = 0
            errors = []

            for stmt in statements:
                stmt = stmt.strip()
                if not stmt:
                    continue
                # ⭐ فیلتر بهتر کامنت‌ها
                if self._is_comment_only(stmt):
                    continue

                try:
                    cursor.execute(stmt)
                    executed += 1
                except MySQLError as e:
                    errors.append(f"دستور #{executed + 1}: {e}")
                    # ادامه بده — بقیه رو اجرا کن
                    continue

            self._conn.commit()
            cursor.close()

            if errors:
                err_text = "\n".join(errors[:3])
                return True, (
                    f"⚠️ {executed} دستور اجرا شد، "
                    f"{len(errors)} خطا:\n{err_text}"
                )

            return True, f"✅ {executed} دستور اجرا شد"

        except MySQLError as e:
            try:
                self._conn.rollback()
            except Exception:
                pass
            return False, f"خطای SQL: {e}"

    @staticmethod
    def _is_comment_only(stmt: str) -> bool:
        """چک کن آیا فقط کامنت هست"""
        lines = stmt.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("--") or line.startswith("#"):
                continue
            if line.startswith("/*") and line.endswith("*/"):
                continue
            return False   # خط غیرکامنت پیدا شد
        return True

    @staticmethod
    def _split_sql(sql: str) -> list[str]:
        """
        تقسیم SQL به دستورات.
        نسخه‌ی جدید: خط‌به‌خط، حذف کامنت‌ها، جدا کردن با ';'
        """
        statements = []
        current = []

        in_string = False
        string_char = None
        in_block_comment = False

        i = 0
        while i < len(sql):
            ch = sql[i]
            next_ch = sql[i + 1] if i + 1 < len(sql) else ""

            # ─── block comment ───
            if not in_string and not in_block_comment:
                if ch == "/" and next_ch == "*":
                    in_block_comment = True
                    i += 2
                    continue
            if in_block_comment:
                if ch == "*" and next_ch == "/":
                    in_block_comment = False
                    i += 2
                    continue
                i += 1
                continue

            # ─── line comment ───
            if not in_string:
                if ch == "-" and next_ch == "-":
                    # تا آخر خط رد کن
                    while i < len(sql) and sql[i] != "\n":
                        i += 1
                    continue
                if ch == "#":
                    while i < len(sql) and sql[i] != "\n":
                        i += 1
                    continue

            # ─── string ───
            if not in_string and ch in ("'", '"', "`"):
                in_string = True
                string_char = ch
                current.append(ch)
                i += 1
                continue

            if in_string:
                if ch == "\\" and next_ch:
                    current.append(ch)
                    current.append(next_ch)
                    i += 2
                    continue
                if ch == string_char:
                    if next_ch == string_char:
                        current.append(ch)
                        current.append(ch)
                        i += 2
                        continue
                    in_string = False
                    string_char = None
                current.append(ch)
                i += 1
                continue

            # ─── end of statement ───
            if ch == ";":
                stmt = "".join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
                i += 1
                continue

            current.append(ch)
            i += 1

        stmt = "".join(current).strip()
        if stmt:
            statements.append(stmt)

        return statements

    # ═════════════════════════════════════════════
    def list_databases(self) -> tuple[bool, list[str]]:
        if not self.is_connected():
            return False, []
        try:
            cursor = self._conn.cursor()
            cursor.execute("SHOW DATABASES")
            result = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return True, result
        except Exception:
            return False, []

    @staticmethod
    def test_connection(host: str, port: int, user: str,
                        password: str) -> tuple[bool, str]:
        try:
            conn = mysql.connector.connect(
                host=host, port=port, user=user, password=password,
                connection_timeout=5,
            )
            ver = conn.get_server_info()
            conn.close()
            return True, f"✅ MySQL {ver}"
        except MySQLError as e:
            return False, f"❌ {e}"
        except Exception as e:
            return False, f"❌ {e}"