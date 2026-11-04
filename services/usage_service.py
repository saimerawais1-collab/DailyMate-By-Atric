
from database import get_usage, increment_usage, is_premium
from config import (
    FREE_DAILY_AI_LIMIT,
    FREE_DAILY_TEXT_LIMIT,
    FREE_DAILY_VOICE_LIMIT,
)


LIMITS = {
    "ai": FREE_DAILY_AI_LIMIT,
    "text": FREE_DAILY_TEXT_LIMIT,
    "voice": FREE_DAILY_VOICE_LIMIT,
}


def check_limit(user_id: int, feature: str) -> bool:
    """
    Returns True if the user is allowed to use the feature.
    """

    if is_premium(user_id):
        return True

    if feature not in LIMITS:
        return False

    usage = get_usage(user_id)

    if not usage:
        return True

    indexes = {
        "ai": 0,
        "text": 1,
        "voice": 2,
    }

    count = usage[indexes[feature]]

    return count < LIMITS[feature]


def record_usage(user_id: int, feature: str):
    if feature in LIMITS:
        increment_usage(user_id, feature)


def get_remaining(user_id: int, feature: str):
    if feature not in LIMITS:
        return 0

    if is_premium(user_id):
        return "Unlimited"

    usage = get_usage(user_id)

    if not usage:
        return LIMITS[feature]

    indexes = {
        "ai": 0,
        "text": 1,
        "voice": 2,
    }

    count = usage[indexes[feature]]

    return max(0, LIMITS[feature] - count)
