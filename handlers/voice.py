
from telegram import Update
from telegram.ext import ContextTypes

from database import get_usage, increment_usage, is_premium
from config import FREE_DAILY_VOICE_LIMIT


async def voice_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [{"text": "🎙 Voice to Text", "callback_data": "voice_transcribe"}],
        [{"text": "🔊 Text to Speech", "callback_data": "voice_tts"}],
        [{"text": "📝 Voice Summary", "callback_data": "voice_summary"}],
    ]

    from telegram import InlineKeyboardMarkup

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
    context.user_data["voice_action"] = action

    if action == "tts":
        await query.message.reply_text(
            "🔊 Send the text you want converted to speech.\n"
            "TTS provider integration will be added later."
        )
    else:
        await query.message.reply_text(
            "🎙 Send a voice message or audio file.\n\n"
            "Voice transcription provider integration "
            "will be added in the next stage."
        )


async def voice_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id

    action = context.user_data.get("voice_action")

    if not action:
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
        text = update.message.text

        if not text:
            await update.message.reply_text(
                "Please send text for speech conversion."
            )
            return

        await update.message.reply_text(
            "🔊 Text-to-speech integration is not connected yet."
        )

    else:
        if not update.message.voice and not update.message.audio:
            await update.message.reply_text(
                "Please send a voice message or audio file."
            )
            return

        await update.message.reply_text(
            "🎙 Voice processing service is not connected yet."
        )

    increment_usage(user_id, "voice")
