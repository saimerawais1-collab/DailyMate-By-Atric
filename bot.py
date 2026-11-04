
import os
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

WELCOME_TEXT = """
✨ Welcome to Daily-Mate By Atric!

One Message. Multiple Solutions.

Your AI-powered daily services assistant.

Choose a service below to get started.
"""

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("🤖 AI Assistant", callback_data="ai"),
            InlineKeyboardButton("🎙 Voice Tools", callback_data="voice"),
        ],
        [
            InlineKeyboardButton("🛠 Daily Utilities", callback_data="utilities"),
            InlineKeyboardButton("📝 Text Tools", callback_data="text"),
        ],
        [
            InlineKeyboardButton("💎 Premium", callback_data="premium"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=main_menu()
    )


async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    messages = {
        "ai": "🤖 AI Assistant\n\nAI features are coming soon!",
        "voice": "🎙 Voice Tools\n\nVoice-to-text is coming soon!",
        "utilities": "🛠 Daily Utilities\n\nUseful daily tools are coming soon!",
        "text": "📝 Text Tools\n\nText processing tools are coming soon!",
        "premium": (
            "💎 Daily-Mate Premium\n\n"
            "Unlock advanced AI tools, higher limits, "
            "and exclusive features.\n\n"
            "Premium subscriptions are coming soon!"
        ),
        "help": (
            "ℹ️ Daily-Mate Help\n\n"
            "Use the menu to explore our services.\n"
            "For support, contact our team soon."
        ),
    }

    message = messages.get(
        query.data,
        "Please select a valid option."
    )

    await query.edit_message_text(
        message,
        reply_markup=main_menu()
    )


async def unknown_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "Please choose a service from the menu.",
        reply_markup=main_menu()
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing!")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message)
    )

    print("Daily-Mate By Atric is starting...")

    app.run_polling()


if __name__ == "__main__":
    main()
