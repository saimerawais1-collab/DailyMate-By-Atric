
import os

# Telegram bot token from GitHub Secrets
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Groq API key (will be added later)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Bot settings
BOT_NAME = "Daily-Mate By Atric"
BOT_TAGLINE = "One Message. Multiple Solutions."

# Database
DATABASE_PATH = "daily_mate.db"

# Free tier limits (initial values; configurable later)
FREE_DAILY_AI_LIMIT = 10
FREE_DAILY_TEXT_LIMIT = 20
FREE_DAILY_VOICE_LIMIT = 5

# Premium settings
PREMIUM_ENABLED = True

# Admin Telegram IDs (add yours later)
ADMIN_IDS = []

# Timezone
DEFAULT_TIMEZONE = "Asia/Karachi"
