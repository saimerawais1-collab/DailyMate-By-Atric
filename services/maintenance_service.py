
from typing import Any

MAINTENANCE_KEY = "maintenance_mode"


def is_maintenance_enabled(bot_data: dict[str, Any]) -> bool:
    return bool(bot_data.get(MAINTENANCE_KEY, False))


def set_maintenance(
    bot_data: dict[str, Any],
    enabled: bool,
) -> None:
    bot_data[MAINTENANCE_KEY] = enabled


def maintenance_message() -> str:
    return (
        "🛠 Daily-Mate By Atric is currently undergoing maintenance.\n\n"
        "Please try again later. Thank you for your patience!"
    )
