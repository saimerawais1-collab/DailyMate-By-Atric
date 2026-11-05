
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
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

    context.user_data["mode"] = "text"
    context.user_data["text_action"] = action
    context.user_data.pop("translate_source", None)
    context.user_data.pop("awaiting_translate_language", None)

    if action == "translate":
        message = (
            "🌐 Translation selected.\n\n"
            "First send the text you want translated.\n"
            "Then I will ask for the target language."
        )
    elif action == "wordcount":
        message = (
            "🔢 Word Counter selected.\n\n"
            "Send the text you want counted."
        )
    else:
        message = (
            f"Selected: {action.title()}\n\n"
            "Now send the text you want me to process.\n\n"
            "To cancel, send /cancel."
        )

    await query.message.reply_text(message)


async def text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    text = update.message.text.strip()

    if not text:
        await update.message.reply_text("Please send some text.")
        return

    # Step 2 of translation: receive target language.
    if context.user_data.get("awaiting_translate_language"):
        source_text = context.user_data.get("translate_source", "")
        language = text

        context.user_data.pop("awaiting_translate_language", None)
        context.user_data.pop("translate_source", None)

        await process_text(
            update,
            context,
            user_id,
            f"Translate the following text into {language}. "
            "Return only the translation, without explanations.\n\n"
            f"{source_text}",
        )
        return

    action = context.user_data.get("text_action")

    if not action:
        return

    # Word counter works locally; no AI/API needed.
    if action == "wordcount":
        words = text.split()
        characters = len(text)
        characters_no_spaces = len("".join(text.split()))
        lines = len(text.splitlines())

        await update.message.reply_text(
            "🔢 Text Statistics\n\n"
            f"Words: {len(words)}\n"
            f"Characters (with spaces): {characters}\n"
            f"Characters (without spaces): {characters_no_spaces}\n"
            f"Lines: {lines}"
        )

        context.user_data.pop("text_action", None)
        context.user_data["mode"] = None
        return

    if action not in TEXT_ACTIONS:
        await update.message.reply_text("Unknown text tool.")
        return

    # Step 1 of translation: save text and ask target language.
    if action == "translate":
        context.user_data["translate_source"] = text
        context.user_data["awaiting_translate_language"] = True

        await update.message.reply_text(
            "🌐 Which language should I translate it into?\n\n"
            "Example: Urdu, English, Arabic, French\n\n"
            "Send the language name now."
        )
        return

    premium = is_premium(user_id)
    usage = get_usage(user_id)
    text_count = usage[1] if usage else 0

    if not premium and text_count >= FREE_DAILY_TEXT_LIMIT:
        await update.message.reply_text(
            "⚠️ Daily Text Tools limit reached.\n"
            "Upgrade to Premium for higher limits."
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
    premium = is_premium(user_id)
    usage = get_usage(user_id)
    text_count = usage[1] if usage else 0

    if not premium and text_count >= FREE_DAILY_TEXT_LIMIT:
        await update.message.reply_text(
            "⚠️ Daily Text Tools limit reached.\n"
            "Upgrade to Premium for higher limits."
        )
        context.user_data.pop("text_action", None)
        context.user_data["mode"] = None
        return

    status_message = await update.message.reply_text(
        "✍️ Processing..."
    )

    try:
        result = await ask_ai(prompt)

    except AIServiceError as error:
        await status_message.edit_text(
            f"⚠️ {error}\n\n"
            "Your daily Text Tools limit has not been used."
        )
        return

    except Exception:
        await status_message.edit_text(
            "⚠️ Something went wrong. Please try again later.\n\n"
            "Your daily Text Tools limit has not been used."
        )
        return

    increment_usage(user_id, "text")

    await status_message.edit_text(result)

    context.user_data.pop("text_action", None)
    context.user_data.pop("translate_source", None)
    context.user_data.pop("awaiting_translate_language", None)
    context.user_data["mode"] = None
