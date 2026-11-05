
from telegram import Update
from telegram.ext import ContextTypes

from services.groq_service import ask_ai, AIServiceError
from database import get_usage, increment_usage, is_premium
from config import FREE_DAILY_AI_LIMIT


MAX_PROMPT_LENGTH = 12000
TELEGRAM_MESSAGE_LIMIT = 4000


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
    message = update.effective_message
    user = update.effective_user

    if not message or not message.text or not user:
        return

    prompt = message.text.strip()

    if not prompt:
        return

    if len(prompt) > MAX_PROMPT_LENGTH:
        await message.reply_text(
            "⚠️ Your message is too long.\n"
            f"Please keep it under {MAX_PROMPT_LENGTH:,} characters."
        )
        return

    premium = is_premium(user.id)

    usage = get_usage(user.id)
    ai_count = usage[0] if usage else 0

    if not premium and ai_count >= FREE_DAILY_AI_LIMIT:
        await message.reply_text(
            "⚠️ You have reached your daily AI limit.\n\n"
            "Premium users get higher usage limits."
        )
        return

    status_message = await message.reply_text("🤔 Thinking...")

    try:
        response = await ask_ai(prompt)

        if not response or not response.strip():
            raise AIServiceError("The AI returned an empty response.")

        increment_usage(user.id, "ai")

        chunks = [
            response[i:i + TELEGRAM_MESSAGE_LIMIT]
            for i in range(0, len(response), TELEGRAM_MESSAGE_LIMIT)
        ]

        await status_message.edit_text(chunks[0])

        for chunk in chunks[1:]:
            await message.reply_text(chunk)

    except AIServiceError as error:
        await status_message.edit_text(
            f"⚠️ {error}\n\n"
            "Your daily AI limit has not been used."
        )

    except Exception:
        await status_message.edit_text(
            "⚠️ Something went wrong. Please try again later."
        )
