
from telegram import Update
from telegram.ext import ContextTypes

from services.groq_service import ask_ai
from database import get_usage, increment_usage, is_premium
from config import FREE_DAILY_TEXT_LIMIT


TEXT_ACTIONS = {
    "grammar": "Correct grammar and spelling while preserving meaning.",
    "summarize": "Summarize the following text clearly.",
    "translate": "Translate the following text. Detect its language and ask for target language if needed.",
    "email": "Turn the following request into a professional email.",
    "caption": "Create engaging social media captions for this content.",
    "hashtags": "Generate relevant and useful hashtags for this content.",
    "rewrite": "Rewrite this text to make it clearer and more polished.",
}


async def text_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [{"text": "📝 Grammar", "callback_data": "text_grammar"},
         {"text": "📄 Summarize", "callback_data": "text_summarize"}],
        [{"text": "🌐 Translate", "callback_data": "text_translate"},
         {"text": "📧 Email", "callback_data": "text_email"}],
        [{"text": "📱 Caption", "callback_data": "text_caption"},
         {"text": "#️⃣ Hashtags", "callback_data": "text_hashtags"}],
        [{"text": "✍️ Rewrite", "callback_data": "text_rewrite"}],
    ]

    from telegram import InlineKeyboardMarkup
    markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        "✍️ Choose a Text Tool:",
        reply_markup=markup,
    )


async def text_action_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    action = query.data.replace("text_", "", 1)

    if action not in TEXT_ACTIONS:
        await query.message.reply_text("Unknown text tool.")
        return

    context.user_data["mode"] = "text"
    context.user_data["text_action"] = action

    await query.message.reply_text(
        f"Selected: {action.title()}\n\n"
        "Now send the text you want me to process."
    )


async def text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id
    text = update.message.text

    action = context.user_data.get("text_action")

    if not action or action not in TEXT_ACTIONS:
        return

    premium = is_premium(user_id)
    usage = get_usage(user_id)
    text_count = usage[1] if usage else 0

    if not premium and text_count >= FREE_DAILY_TEXT_LIMIT:
        await update.message.reply_text(
            "⚠️ Daily Text Tools limit reached. "
            "Upgrade to Premium for higher limits."
        )
        return

    prompt = f"{TEXT_ACTIONS[action]}\n\n{text}"

    await update.message.reply_text("✍️ Processing...")

    result = await ask_ai(prompt)

    increment_usage(user_id, "text")

    await update.message.reply_text(result)

    context.user_data.pop("text_action", None)
    context.user_data["mode"] = None
