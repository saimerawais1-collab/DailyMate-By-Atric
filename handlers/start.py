
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from database import register_user
from config import BOT_NAME, BOT_TAGLINE
from handlers.referrals import register_referral


def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("🤖 AI Assistant", callback_data="ai"),
            InlineKeyboardButton("✍️ Text Tools", callback_data="text"),
        ],
        [
            InlineKeyboardButton("🎙 Voice Tools", callback_data="voice"),
            InlineKeyboardButton("🧰 Daily Utilities", callback_data="utilities"),
        ],
        [
            InlineKeyboardButton("⭐ Premium", callback_data="premium"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    register_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )

    # Process referral start parameter
    if context.args:
        referral_arg = context.args[0]

        if referral_arg.startswith("ref_"):
            try:
                referrer_id = int(referral_arg.replace("ref_", "", 1))
                register_referral(
                    new_user_id=user.id,
                    referrer_id=referrer_id,
                )
            except ValueError:
                pass

    message = (
        f"Welcome to {BOT_NAME}, {user.first_name}!\n\n"
        f"{BOT_TAGLINE}\n\n"
        "Your daily AI-powered assistant is here.\n"
        "Choose a service below:"
    )

    await update.message.reply_text(
        message,
        reply_markup=main_menu(),
    )