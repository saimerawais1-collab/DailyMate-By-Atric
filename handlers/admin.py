
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS, DATABASE_PATH
import sqlite3


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def admin_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text(
            "⛔ You are not authorized to use admin commands."
        )
        return

    await update.message.reply_text(
        "🛠 Daily-Mate Admin Panel\n\n"
        "/stats - Bot statistics\n"
        "/maintenance - Toggle maintenance mode\n"
        "/adminhelp - Admin command help"
    )


async def admin_help(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Access denied.")
        return

    await update.message.reply_text(
        "🛠 Admin Commands\n\n"
        "/admin - Admin panel\n"
        "/stats - User and usage statistics\n"
        "/maintenance - Toggle maintenance mode\n"
        "/adminhelp - Show this help"
    )


async def stats_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Access denied.")
        return

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            user_count = conn.execute(
                "SELECT COUNT(*) FROM users"
            ).fetchone()[0]

            premium_count = conn.execute(
                "SELECT COUNT(*) FROM users WHERE is_premium = 1"
            ).fetchone()[0]

            today_usage = conn.execute(
                "SELECT COALESCE(SUM(ai_count), 0), "
                "COALESCE(SUM(text_count), 0), "
                "COALESCE(SUM(voice_count), 0) "
                "FROM usage WHERE usage_date = date('now')"
            ).fetchone()

        await update.message.reply_text(
            "📊 Daily-Mate Statistics\n\n"
            f"👥 Total users: {user_count}\n"
            f"⭐ Premium users: {premium_count}\n\n"
            f"🤖 AI uses today: {today_usage[0]}\n"
            f"✍️ Text uses today: {today_usage[1]}\n"
            f"🎙 Voice uses today: {today_usage[2]}"
        )

    except Exception as error:
        print(f"Stats error: {error}")
        await update.message.reply_text(
            "Could not retrieve statistics."
        )


async def maintenance_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Access denied.")
        return

    current = context.bot_data.get("maintenance", False)
    context.bot_data["maintenance"] = not current

    status = "ON" if not current else "OFF"

    await update.message.reply_text(
        f"🔧 Maintenance mode: {status}"
    )
