

import logging
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN
from database import init_db

from handlers.start import start_command
from handlers.ai import ai_callback, ai_message
from handlers.text_tools import text_callback, text_action_callback, text_message
from handlers.voice import voice_callback, voice_action_callback, voice_message
from handlers.utilities import (
    utilities_callback,
    utility_action_callback,
    utility_message,
)
from handlers.premium import (
    premium_callback,
    premium_features_callback,
    premium_plans_callback,
    premium_usage_callback,
)
from handlers.help import help_command, menu_command
from handlers.referrals import referral_command
from handlers.admin import (
    admin_command,
    admin_help,
    stats_command,
    maintenance_command,
)
from handlers.misc import (
    feedback_command,
    feedback_message,
    sponsor_command,
    sponsor_info_callback,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


async def cancel_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.clear()

    await update.message.reply_text(
        "❌ Current task cancelled.\n\n"
        "Use /menu to choose another service."
    )


async def message_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    # Feedback mode
    if context.user_data.get("awaiting_feedback"):
        await feedback_message(update, context)
        return

    mode = context.user_data.get("mode")

    # AI Assistant
    if mode == "ai" and update.message.text:
        await ai_message(update, context)
        return

    # Text Tools
    if mode == "text" and update.message.text:
        await text_message(update, context)
        return

    # Voice Tools
    if mode == "voice":
        await voice_message(update, context)
        return

    # Daily Utilities
    if context.user_data.get("utility_action"):
        await utility_message(update, context)
        return

    await update.message.reply_text(
        "Please choose a service from /menu first."
    )


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    logger.error("Bot error: %s", context.error)


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is missing from GitHub Actions Secrets."
        )

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("referral", referral_command))
    app.add_handler(CommandHandler("premium", premium_callback))
    app.add_handler(CommandHandler("feedback", feedback_command))
    app.add_handler(CommandHandler("sponsor", sponsor_command))

    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("adminhelp", admin_help))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("maintenance", maintenance_command))

    # Main menu callback buttons
    app.add_handler(CallbackQueryHandler(ai_callback, pattern=r"^ai$"))
    app.add_handler(CallbackQueryHandler(text_callback, pattern=r"^text$"))
    app.add_handler(CallbackQueryHandler(voice_callback, pattern=r"^voice$"))
    app.add_handler(
        CallbackQueryHandler(utilities_callback, pattern=r"^utilities$")
    )
    app.add_handler(
        CallbackQueryHandler(premium_callback, pattern=r"^premium$")
    )
    app.add_handler(CallbackQueryHandler(help_command, pattern=r"^help$"))

    # Text tool callbacks
    app.add_handler(
        CallbackQueryHandler(text_action_callback, pattern=r"^text_[a-z]+$")
    )

    # Voice tool callbacks
    app.add_handler(
        CallbackQueryHandler(voice_action_callback, pattern=r"^voice_(transcribe|tts|summary)$")
    )

    # Utility callbacks
    app.add_handler(
        CallbackQueryHandler(utility_action_callback, pattern=r"^util_(calc|date|unit|currency|qr)$")
    )

    # Premium callbacks
    app.add_handler(
        CallbackQueryHandler(premium_features_callback, pattern=r"^premium_features$")
    )
    app.add_handler(
        CallbackQueryHandler(premium_plans_callback, pattern=r"^premium_plans$")
    )
    app.add_handler(
        CallbackQueryHandler(premium_usage_callback, pattern=r"^premium_usage$")
    )

    # Misc callback
    app.add_handler(
        CallbackQueryHandler(sponsor_info_callback, pattern=r"^sponsor_info$")
    )

    # Messages
    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.VOICE | filters.AUDIO) & ~filters.COMMAND,
            message_router,
        )
    )

    app.add_error_handler(error_handler)

    logger.info("Daily-Mate By Atric is starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
