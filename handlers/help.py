
from telegram import Update
from telegram.ext import ContextTypes


HELP_TEXT = """
ℹ️ Daily-Mate By Atric — Help

One Message. Multiple Solutions.

🤖 AI Assistant
Ask questions, write content, brainstorm, and get help.

✍️ Text Tools
• Grammar correction
• Summarization
• Translation
• Email writing
• Social captions
• Hashtags
• Text rewriting

🎙 Voice Tools
• Voice-to-text
• Text-to-speech
• Voice summaries

🧰 Daily Utilities
• Calculator
• Currency converter
• Unit converter
• Date calculator
• QR generator
• More tools coming soon

⭐ Premium
Higher limits and advanced features.

🎁 Referrals
Invite friends using your personal referral link.

Commands:
/start - Open the bot
/menu - Show main menu
/help - Show this help
/referral - Get your invite link
/premium - Premium options
"""


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(HELP_TEXT)


async def menu_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    from handlers.start import main_menu

    await update.message.reply_text(
        "🏠 Daily-Mate Main Menu",
        reply_markup=main_menu(),
    )
