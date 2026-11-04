

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from database import get_usage, is_premium
from config import FREE_DAILY_VOICE_LIMIT


async def voice_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "🎙 Voice to Text",
                callback_data="voice_transcribe",
            )
        ],
        [
            InlineKeyboardButton(
                "🔊 Text to Speech",
                callback_data="voice_tts",
            )
        ],
        [
            InlineKeyboardButton(
                "📝 Voice Summary",
                callback_data="voice_summary",
            )
        ],
    ]

    await query.message.reply_text(
        "🎙 Voice Tools\n\nChoose a service:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def voice_action_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    action = query.data.replace("voice_", "", 1)

    if action not in {"transcribe", "tts", "summary"}:
        await query.message.reply_text("Unknown voice tool.")
        return

    context.user_data["mode"] = "voice"
    context.user_data["voice_action"] = action

    if action == "tts":
        await query.message.reply_text(
            "🔊 Send the text you want converted to speech.\n\n"
            "TTS provider integration is not connected yet."
        )
    else:
        await query.message.reply_text(
            "🎙 Send a voice message or audio file.\n\n"
            "Voice transcription and summary services "
            "are not connected yet."
        )


async def voice_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    user_id = update.effective_user.id
    action = context.user_data.get("voice_action")

    if action not in {"transcribe", "tts", "summary"}:
        return

    premium = is_premium(user_id)
    usage = get_usage(user_id)
    voice_count = usage[2] if usage else 0

    if not premium and voice_count >= FREE_DAILY_VOICE_LIMIT:
        await update.message.reply_text(
            "⚠️ Daily Voice Tools limit reached.\n"
            "Premium users get higher limits."
        )
        return

    if action == "tts":
        if not update.message.text:
            await update.message.reply_text(
                "Please send text for speech conversion."
            )
            return

        await update.message.reply_text(
            "🔊 Text-to-speech provider is not connected yet."
        )

    else:
        if not update.message.voice and not update.message.audio:
            await update.message.reply_text(
                "Please send a Telegram voice message or audio file."
            )
            return

        if action == "transcribe":
            await update.message.reply_text(
                "🎙 Voice transcription provider is not connected yet."
            )
        else:
            await update.message.reply_text(
                "📝 Voice summary provider is not connected yet."
            )

    # Do not consume daily voice usage while the provider is unavailable.
