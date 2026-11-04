
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import (
    FREE_DAILY_AI_LIMIT,
    FREE_DAILY_TEXT_LIMIT,
    FREE_DAILY_VOICE_LIMIT,
)


def premium_menu():
    keyboard = [
        [
            InlineKeyboardButton(
                "💎 Premium Features",
                callback_data="premium_features",
            )
        ],
        [
            InlineKeyboardButton(
                "💳 Subscription Plans",
                callback_data="premium_plans",
            )
        ],
        [
            InlineKeyboardButton(
                "📊 My Usage",
                callback_data="premium_usage",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def premium_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "⭐ Daily-Mate Premium\n\n"
        "Unlock higher limits and advanced services.\n\n"
        "Choose an option:",
        reply_markup=premium_menu(),
    )


async def premium_features_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "💎 Premium Benefits\n\n"
        "• Higher AI usage limits\n"
        "• Higher Text Tools limits\n"
        "• Higher Voice Tools limits\n"
        "• Ad-free experience\n"
        "• Advanced AI features\n"
        "• Priority access to selected tools\n\n"
        "More benefits will be added as the platform grows."
    )


async def premium_plans_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "💳 Premium Subscription\n\n"
        "Subscription plans and secure payment integration "
        "will be configured before launch.\n\n"
        "No payment is being collected right now."
    )


async def premium_usage_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    from database import get_usage, is_premium

    user_id = update.effective_user.id
    usage = get_usage(user_id)

    ai_count = usage[0] if usage else 0
    text_count = usage[1] if usage else 0
    voice_count = usage[2] if usage else 0

    premium = is_premium(user_id)

    if premium:
        limits = "Premium account: elevated limits."
    else:
        limits = (
            f"AI: {ai_count}/{FREE_DAILY_AI_LIMIT}\n"
            f"Text: {text_count}/{FREE_DAILY_TEXT_LIMIT}\n"
            f"Voice: {voice_count}/{FREE_DAILY_VOICE_LIMIT}"
        )

    await query.message.reply_text(
        "📊 Your Daily Usage\n\n"
        f"{limits}"
    )
