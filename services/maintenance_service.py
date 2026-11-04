

import sqlite3

from config import DATABASE_PATH


MAINTENANCE_KEY = "maintenance_mode"


def _ensure_table():
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL
            )
        """)
        conn.commit()


def is_maintenance_enabled(bot_data=None) -> bool:
    _ensure_table()

    with sqlite3.connect(DATABASE_PATH) as conn:
        result = conn.execute(
            """
            SELECT setting_value
            FROM bot_settings
            WHERE setting_key = ?
            """,
            (MAINTENANCE_KEY,),
        ).fetchone()

    return bool(result and result[0] == "1")


def set_maintenance(bot_data, enabled: bool) -> None:
    _ensure_table()

    value = "1" if enabled else "0"

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            INSERT INTO bot_settings (setting_key, setting_value)
            VALUES (?, ?)
            ON CONFLICT(setting_key)
            DO UPDATE SET setting_value = excluded.setting_value
            """,
            (MAINTENANCE_KEY, value),
        )
        conn.commit()


def maintenance_message() -> str:
    return (
        "🛠 Daily-Mate By Atric is currently undergoing maintenance.\n\n"
        "Please try again later. Thank you for your patience!"
    )
