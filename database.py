
import sqlite3
from datetime import date
from config import DATABASE_PATH


def get_connection():
    return sqlite3.connect(DATABASE_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at TEXT,
                is_premium INTEGER DEFAULT 0,
                premium_until TEXT,
                referred_by INTEGER DEFAULT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS usage (
                user_id INTEGER,
                usage_date TEXT,
                ai_count INTEGER DEFAULT 0,
                text_count INTEGER DEFAULT 0,
                voice_count INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, usage_date)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                referrer_id INTEGER,
                referred_id INTEGER UNIQUE,
                created_at TEXT
            )
        """)

        conn.commit()


def register_user(user_id, username=None, first_name=None):
    with get_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO users
            (user_id, username, first_name, joined_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, first_name, date.today().isoformat()))

        conn.execute("""
            UPDATE users
            SET username = ?, first_name = ?
            WHERE user_id = ?
        """, (username, first_name, user_id))

        conn.commit()


def get_user(user_id):
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        return cursor.fetchone()


def is_premium(user_id):
    user = get_user(user_id)

    if not user:
        return False

    return bool(user[4])


def get_usage(user_id):
    today = date.today().isoformat()

    with get_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO usage (user_id, usage_date)
            VALUES (?, ?)
        """, (user_id, today))

        cursor = conn.execute("""
            SELECT ai_count, text_count, voice_count
            FROM usage
            WHERE user_id = ? AND usage_date = ?
        """, (user_id, today))

        conn.commit()
        return cursor.fetchone()


def increment_usage(user_id, usage_type):
    today = date.today().isoformat()

    allowed_columns = {
        "ai": "ai_count",
        "text": "text_count",
        "voice": "voice_count"
    }

    column = allowed_columns.get(usage_type)

    if not column:
        return

    with get_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO usage (user_id, usage_date)
            VALUES (?, ?)
        """, (user_id, today))

        conn.execute(
            f"UPDATE usage SET {column} = {column} + 1 "
            "WHERE user_id = ? AND usage_date = ?",
            (user_id, today)
        )

        conn.commit()
