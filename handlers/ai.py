
from telegram import Update
from telegram.ext import ContextTypes

from services.groq_service import ask_ai
from database import get_usage, increment_usage, is_premium
from config import FREE_DAILY_AI_LIMIT


async def ai_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    context.user_data["mode"] = "ai"

    await query.message.reply_text(
        "🤖 AI Assistant activated!\n\n"
        "Send me your question or task.\n"
        "Type /menu to return to the main menu."
    )


async def ai_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id
    prompt = update.message.text

    if not prompt:
        return

    premium = is_premium(user_id)

    usage = get_usage(user_id)
    ai_count = usage[0] if usage else 0

    if not premium and ai_count >= FREE_DAILY_AI_LIMIT:
        await update.message.reply_text(
            "⚠️ You have reached your daily AI limit.\n\n"
            "Premium users get higher usage limits."
        )
        return

    await update.message.reply_text("🤔 Thinking...")

    response = await ask_ai(prompt)

    increment_usage(user_id, "ai")

    await update.message.reply_text(response)
