

import sqlite3
from datetime import date, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS, DATABASE_PATH
from database import get_today
from services.maintenance_service import (
    is_maintenance_enabled,
    set_maintenance,
)


def is_admin(user_id):
    return user_id in ADMIN_IDS


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin access only.")
        return

    await update.message.reply_text(
        "🛠 Daily-Mate Admin Panel\n\n"
        "/adminhelp - Admin commands\n"
        "/stats - Bot statistics\n"
        "/maintenance on - Enable maintenance\n"
        "/maintenance off - Disable maintenance\n"
        "/grantpremium USER_ID DAYS - Grant premium\n"
        "/revokepremium USER_ID - Revoke premium"
    )


async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin access only.")
        return

    await update.message.reply_text(
        "📚 ADMIN COMMANDS\n\n"
        "/admin - Open admin panel\n"
        "/adminhelp - Show this help\n"
        "/stats - View bot statistics\n"
        "/maintenance on - Enable maintenance\n"
        "/maintenance off - Disable maintenance\n"
        "/grantpremium USER_ID DAYS - Grant premium\n"
        "/revokepremium USER_ID - Revoke premium\n\n"
        "Example:\n"
        "/grantpremium 123456789 30"
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin access only.")
        return

    today = get_today()

    with sqlite3.connect(DATABASE_PATH) as conn:
        total_users = conn.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

        premium_users = conn.execute(
            "SELECT COUNT(*) FROM users WHERE is_premium = 1"
        ).fetchone()[0]

        usage = conn.execute(
            """
            SELECT
                COALESCE(SUM(ai_count), 0),
                COALESCE(SUM(text_count), 0),
                COALESCE(SUM(voice_count), 0)
            FROM usage
            WHERE usage_date = ?
            """,
            (today,),
        ).fetchone()

    await update.message.reply_text(
        "📊 DAILY-MATE BOT STATS\n\n"
        f"👥 Total users: {total_users}\n"
        f"⭐ Premium users: {premium_users}\n\n"
        f"🤖 AI requests today: {usage[0]}\n"
        f"📝 Text requests today: {usage[1]}\n"
        f"🎙 Voice requests today: {usage[2]}"
    )


async def maintenance_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin access only.")
        return

    if not context.args or context.args[0].lower() not in ("on", "off"):
        await update.message.reply_text(
            "Usage:\n/maintenance on\n/maintenance off"
        )
        return

    enabled = context.args[0].lower() == "on"
    set_maintenance(context.bot_data, enabled)

    status = "ENABLED 🔴" if enabled else "DISABLED 🟢"
    await update.message.reply_text(
        f"Maintenance mode {status}"
    )


async def grant_premium_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin access only.")
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "Usage:\n/grantpremium USER_ID DAYS\n\n"
            "Example:\n/grantpremium 123456789 30"
        )
        return

    try:
        target_id = int(context.args[0])
        days = int(context.args[1])
        if target_id <= 0 or not 1 <= days <= 3650:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "Invalid user ID or days. Days must be between 1 and 3650."
        )
        return

    today = date.fromisoformat(get_today())

    with sqlite3.connect(DATABASE_PATH) as conn:
        user = conn.execute(
            """
            SELECT is_premium, premium_until
            FROM users
            WHERE user_id = ?
            """,
            (target_id,),
        ).fetchone()

        if not user:
            await update.message.reply_text(
                "User not found. They must start the bot first."
            )
            return

        is_premium_flag, premium_until = user

        if is_premium_flag and premium_until:
            try:
                current_expiry = date.fromisoformat(premium_until[:10])
            except ValueError:
                current_expiry = today
        else:
            current_expiry = today

        base_date = max(today, current_expiry)
        new_expiry = base_date + timedelta(days=days)

        conn.execute(
            """
            UPDATE users
            SET is_premium = 1, premium_until = ?
            WHERE user_id = ?
            """,
            (new_expiry.isoformat(), target_id),
        )
        conn.commit()

    await update.message.reply_text(
        "✅ Premium granted successfully!\n\n"
        f"👤 User ID: {target_id}\n"
        f"⏳ Added days: {days}\n"
        f"📅 Premium expiry: {new_expiry.isoformat()}"
    )


async def revoke_premium_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin access only.")
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/revokepremium USER_ID"
        )
        return

    try:
        target_id = int(context.args[0])
        if target_id <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Invalid user ID.")
        return

    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.execute(
            """
            UPDATE users
            SET is_premium = 0, premium_until = NULL
            WHERE user_id = ?
            """,
            (target_id,),
        )
        conn.commit()

    if cursor.rowcount == 0:
        await update.message.reply_text("User not found.")
        return

    await update.message.reply_text(
        "✅ Premium revoked successfully.\n"
        f"👤 User ID: {target_id}"
    )
