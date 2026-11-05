

import os

# Telegram bot token from GitHub Secrets
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Groq API key from GitHub Secrets
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Bot settings
BOT_NAME = "Daily-Mate By Atric"
BOT_TAGLINE = "One Message. Multiple Solutions."

# Database
DATABASE_PATH = "daily_mate.db"

# Free tier daily limits
FREE_DAILY_AI_LIMIT = 5
FREE_DAILY_TEXT_LIMIT = 10
FREE_DAILY_VOICE_LIMIT = 3

# Premium settings
PREMIUM_ENABLED = True

# Admin Telegram IDs
ADMIN_IDS = [8230920402]

# Timezone
DEFAULT_TIMEZONE = "Asia/Karachi"
