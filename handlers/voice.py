
import asyncio
import logging
from io import BytesIO

from groq import Groq
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from database import (
    get_usage,
    is_premium,
    increment_usage,
)
from config import FREE_DAILY_VOICE_LIMIT, GROQ_API_KEY
from services.groq_service import ask_ai

logger = logging.getLogger(__name__)

TRANSCRIPTION_MODEL = "whisper-large-v3-turbo"
MAX_AUDIO_SIZE = 20 * 1024 * 1024


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
            "🔊 Text-to-Speech\n\n"
            "This service is not connected yet.\n"
            "Voice-to-Text and Voice Summary are available."
        )
    else:
        service_name = (
            "Voice-to-Text"
            if action == "transcribe"
            else "Voice Summary"
        )

        await query.message.reply_text(
            f"🎙 {service_name}\n\n"
            "Send a Telegram voice message or audio file.\n"
            "I will process it using AI."
        )


def _transcribe_audio(audio_bytes: bytes, filename: str) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("Groq API key is not configured.")

    client = Groq(api_key=GROQ_API_KEY)

    result = client.audio.transcriptions.create(
        file=(filename, audio_bytes),
        model=TRANSCRIPTION_MODEL,
        response_format="text",
    )

    if isinstance(result, str):
        transcription = result.strip()
    else:
        transcription = getattr(result, "text", "").strip()

    if not transcription:
        raise ValueError("No speech was detected.")

    return transcription


async def voice_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.message

    if not message:
        return

    user = update.effective_user

    if not user:
        return

    action = context.user_data.get("voice_action")

    if action not in {"transcribe", "tts", "summary"}:
        return

    if action == "tts":
        await message.reply_text(
            "🔊 Text-to-Speech is not connected yet."
        )
        return

    premium = is_premium(user.id)
    usage = get_usage(user.id)
    voice_count = usage[2] if usage else 0

    if not premium and voice_count >= FREE_DAILY_VOICE_LIMIT:
        await message.reply_text(
            "⚠️ Daily Voice Tools limit reached.\n"
            "Premium users get higher limits."
        )
        return

    audio_file = message.voice or message.audio

    if not audio_file:
        await message.reply_text(
            "Please send a Telegram voice message or audio file."
        )
        return

    if audio_file.file_size and audio_file.file_size > MAX_AUDIO_SIZE:
        await message.reply_text(
            "❌ Audio file is too large.\n"
            "Please send a file smaller than 20 MB."
        )
        return

    if not GROQ_API_KEY:
        await message.reply_text(
            "❌ Voice service is not configured. Contact the administrator."
        )
        return

    status = await message.reply_text(
        "⏳ Downloading and processing your audio..."
    )

    try:
        telegram_file = await context.bot.get_file(audio_file.file_id)
        audio_bytes = bytes(
            await telegram_file.download_as_bytearray()
        )

        if len(audio_bytes) > MAX_AUDIO_SIZE:
            await status.edit_text(
                "❌ Audio file is too large. Maximum size is 20 MB."
            )
            return

        if message.voice:
            filename = "voice_message.ogg"
        else:
            filename = audio_file.file_name or "audio_file.mp3"

        transcription = await asyncio.to_thread(
            _transcribe_audio,
            audio_bytes,
            filename,
        )

        if action == "transcribe":
            response = (
                "🎙 **Voice Transcription**\n\n"
                f"{transcription}"
            )

        else:
            await status.edit_text(
                "📝 Audio transcribed. Generating summary..."
            )

            response = await ask_ai(
                "Summarize the following audio transcription. "
                "Preserve its important facts, decisions, and key points. "
                "Use clear bullet points and respond in the same language "
                "as the transcription.\n\n"
                f"TRANSCRIPTION:\n{transcription}"
            )

            response = f"📝 **Voice Summary**\n\n{response}"

        increment_usage(user.id, "voice")

        if len(response) > 4000:
            response = response[:3900] + "\n\n... (text shortened)"

        await status.delete()
        await message.reply_text(
            response,
            parse_mode="Markdown",
        )

    except ValueError:
        await status.edit_text(
            "❌ No clear speech was detected. Please try another recording."
        )

    except Exception as error:
        logger.exception("Voice processing failed: %s", error)

        await status.edit_text(
            "❌ Voice processing failed.\n"
            "Please try again later or send another audio file."
        )
