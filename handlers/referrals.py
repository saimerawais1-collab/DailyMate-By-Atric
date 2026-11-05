import sqlite3

from telegram import Update
from telegram.ext import ContextTypes

from config import DATABASE_PATH
from database import get_today


def get_referral_count(user_id: int) -> int:
    with sqlite3.connect(DATABASE_PATH) as conn:
        result = conn.execute(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?",
            (user_id,),
        ).fetchone()

    return result[0] if result else 0


def register_referral(new_user_id: int, referrer_id: int) -> bool:
    """
    Register a referral only once.
    Users cannot refer themselves.
    """

    if new_user_id == referrer_id:
        return False

    with sqlite3.connect(DATABASE_PATH) as conn:
        existing = conn.execute(
            "SELECT referred_id FROM referrals WHERE referred_id = ?",
            (new_user_id,),
        ).fetchone()

        if existing:
            return False

        referrer_exists = conn.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (referrer_id,),
        ).fetchone()

        if not referrer_exists:
            return False

        conn.execute(
            """
            INSERT INTO referrals
            (referrer_id, referred_id, created_at)
            VALUES (?, ?, ?)
            """,
            (referrer_id, new_user_id, get_today()),
        )

        conn.execute(
            "UPDATE users SET referred_by = ? WHERE user_id = ?",
            (referrer_id, new_user_id),
        )

        conn.commit()

    return True


async def referral_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    message = update.effective_message

    if user is None or message is None:
        return

    bot_username = context.bot.username

    referral_link = (
        f"https://t.me/{bot_username}?start=ref_{user.id}"
    )

    count = get_referral_count(user.id)

    await message.reply_text(
        "🎁 Daily-Mate Referral Program\n\n"
        "Invite friends using your personal link:\n\n"
        f"{referral_link}\n\n"
        f"👥 Successful referrals: {count}\n\n"
        "Referral rewards will be announced when the program launches."
    )
