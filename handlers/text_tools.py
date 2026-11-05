
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.groq_service import ask_ai, AIServiceError
from database import get_usage, increment_usage, is_premium
from config import FREE_DAILY_TEXT_LIMIT


TEXT_ACTIONS = {
    "grammar": "Correct grammar and spelling while preserving meaning.",
    "summarize": "Summarize the following text clearly.",
    "translate": "Translate the following text.",
    "email": "Turn the following request into a professional email.",
    "caption": "Create engaging social media captions for this content.",
    "hashtags": "Generate relevant and useful hashtags for this content.",
    "rewrite": "Rewrite this text to make it clearer and more polished.",
}


def clear_text_state(context):
    context.user_data.pop("text_action", None)
    context.user_data.pop("translate_source", None)
    context.user_data.pop("awaiting_translate_language", None)
    context.user_data["mode"] = None


def text_limit_reached(user_id):
    if is_premium(user_id):
        return False

    usage = get_usage(user_id)
    text_count = usage[1] if usage else 0

    return text_count >= FREE_DAILY_TEXT_LIMIT


async def text_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("📝 Grammar", callback_data="text_grammar"),
            InlineKeyboardButton("📄 Summarize", callback_data="text_summarize"),
        ],
        [
            InlineKeyboardButton("🌐 Translate", callback_data="text_translate"),
            InlineKeyboardButton("📧 Email", callback_data="text_email"),
        ],
        [
            InlineKeyboardButton("📱 Caption", callback_data="text_caption"),
            InlineKeyboardButton(" #️⃣ Hashtags", callback_data="text_hashtags"),
        ],
        [
            InlineKeyboardButton("✍️ Rewrite", callback_data="text_rewrite"),
            InlineKeyboardButton("🔢 Word Counter", callback_data="text_wordcount"),
        ],
    ]

    await query.message.reply_text(
        "✍️ Choose a Text Tool:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def text_action_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    action = query.data.replace("text_", "", 1)

    if action not in TEXT_ACTIONS and action != "wordcount":
        await query.message.reply_text("Unknown text tool.")
        return

    clear_text_state(context)

    context.user_data["mode"] = "text"
    context.user_data["text_action"] = action

    if action == "translate":
        message = (
            "🌐 Translate selected.\n\n"
            "Send the text you want translated first.\n"
            "Then I will ask you for the target language.\n\n"
            "To cancel, send /cancel."
        )

    elif action == "wordcount":
        message = (
            "🔢 Word Counter selected.\n\n"
            "Send the text you want counted.\n\n"
            "To cancel, send /cancel."
        )

    else:
        message = (
            f"Selected: {action.title()}\n\n"
            "Send the text you want me to process.\n\n"
            "To cancel, send /cancel."
        )

    await query.message.reply_text(message)


async def text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.message.text:
        return

    user = update.effective_user

    if not user:
        return

    user_id = user.id
    text = update.message.text.strip()

    if not text:
        await update.message.reply_text("Please send some text.")
        return

    action = context.user_data.get("text_action")

    if not action:
        return

    # Translation: receive target language.
    if context.user_data.get("awaiting_translate_language"):
        source_text = context.user_data.get("translate_source")

        if not source_text:
            clear_text_state(context)
            await update.message.reply_text(
                "Translation session expired. Please select Translate again."
            )
            return

        language = text

        prompt = (
            f"Translate the following text into {language}.\n"
            "Return only the translation. Do not add explanations.\n\n"
            f"{source_text}"
        )

        await process_text(update, context, user_id, prompt)
        return

    # Word Counter.
    if action == "wordcount":
        if text_limit_reached(user_id):
            await update.message.reply_text(
                "⚠️ Daily Text Tools limit reached.\n"
                "Upgrade to Premium for higher limits."
            )
            clear_text_state(context)
            return

        words = text.split()
        lines = text.splitlines()
        characters_without_spaces = len("".join(text.split()))

        await update.message.reply_text(
            "🔢 Text Statistics\n\n"
            f"Words: {len(words)}\n"
            f"Characters (with spaces): {len(text)}\n"
            f"Characters (without whitespace): {characters_without_spaces}\n"
            f"Lines: {len(lines)}"
        )

        increment_usage(user_id, "text")
        clear_text_state(context)
        return

    if action not in TEXT_ACTIONS:
        clear_text_state(context)
        await update.message.reply_text("Unknown text tool.")
        return

    # Translation: receive original text first.
    if action == "translate":
        context.user_data["translate_source"] = text
        context.user_data["awaiting_translate_language"] = True

        await update.message.reply_text(
            "🌐 Which language should I translate it into?\n\n"
            "Examples: Urdu, English, Arabic, French\n\n"
            "Send the target language now."
        )
        return

    prompt = f"{TEXT_ACTIONS[action]}\n\n{text}"

    await process_text(update, context, user_id, prompt)


async def process_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    prompt: str,
):
    if text_limit_reached(user_id):
        await update.message.reply_text(
            "⚠️ Daily Text Tools limit reached.\n"
            "Upgrade to Premium for higher limits."
        )
        clear_text_state(context)
        return

    status_message = await update.message.reply_text("✍️ Processing...")

    try:
        result = await ask_ai(prompt)

        if not isinstance(result, str) or not result.strip():
            raise AIServiceError("AI returned an empty response.")

    except AIServiceError as error:
        await status_message.edit_text(
            f"⚠️ {error}\n\n"
            "Your usage has not been charged.\n"
            "Please try sending your text again."
        )
        return

    except Exception:
        await status_message.edit_text(
            "⚠️ Something went wrong. Please try again later.\n\n"
            "Your usage has not been charged."
        )
        return

    increment_usage(user_id, "text")

    await status_message.edit_text(result)

    clear_text_state(context)