
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def feedback_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["awaiting_feedback"] = True

    await update.message.reply_text(
        "📝 Please send your feedback in your next message.\n\n"
        "Your feedback helps improve Daily-Mate By Atric."
    )


async def feedback_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not context.user_data.get("awaiting_feedback"):
        return

    if not update.message or not update.message.text:
        await update.message.reply_text(
            "Please send feedback as text."
        )
        return

    user = update.effective_user
    feedback = update.message.text.strip()

    if not feedback:
        await update.message.reply_text(
            "Feedback cannot be empty. Please try again."
        )
        return

    context.user_data["awaiting_feedback"] = False

    await update.message.reply_text(
        "✅ Thank you! Your feedback has been received."
    )

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "📩 New Daily-Mate Feedback\n\n"
                    f"User ID: {user.id}\n"
                    f"Username: @{user.username or 'No username'}\n\n"
                    f"Feedback:\n{feedback}"
                ),
            )
        except Exception as error:
            print(f"Could not send feedback to admin {admin_id}: {error}")


async def sponsor_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    sponsor_text = context.bot_data.get("sponsor_message")

    if not sponsor_text:
        await update.message.reply_text(
            "📢 Sponsored promotions are coming soon!\n\n"
            "Businesses will be able to promote their services "
            "through Daily-Mate By Atric."
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "ℹ️ About this promotion",
                callback_data="sponsor_info",
            )
        ]
    ]

    await update.message.reply_text(
        f"📢 Sponsored Message\n\n{sponsor_text}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def sponsor_info_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "This is a sponsored promotion. "
        "Sponsored content is separate from Daily-Mate's AI answers."
    )
