

import ast
import operator
from datetime import date, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


def utilities_menu():
    keyboard = [
        [
            InlineKeyboardButton("🧮 Calculator", callback_data="util_calc"),
            InlineKeyboardButton("📅 Date Tool", callback_data="util_date"),
        ],
        [
            InlineKeyboardButton("📏 Unit Converter", callback_data="util_unit"),
            InlineKeyboardButton("💱 Currency", callback_data="util_currency"),
        ],
        [
            InlineKeyboardButton("🔳 QR Generator", callback_data="util_qr"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def utilities_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "🧰 Daily Utilities\n\nSelect a tool:",
        reply_markup=utilities_menu(),
    )


async def utility_action_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    action = query.data.replace("util_", "", 1)

    if action not in {"calc", "date", "unit", "currency", "qr"}:
        await query.message.reply_text("Unknown utility.")
        return

    context.user_data["utility_action"] = action

    instructions = {
        "calc": "Send a math expression, for example: 25 * (8 + 2)",
        "date": "Send a date as YYYY-MM-DD, for example: 2026-12-25",
        "unit": (
            "Send a conversion like:\n"
            "10 km to miles\n"
            "5 kg to lb\n"
            "100 cm to m"
        ),
        "currency": (
            "Currency conversion is not connected yet.\n"
            "Live exchange rates will be added later."
        ),
        "qr": (
            "QR generation is not connected yet.\n"
            "It will be added in a later integration step."
        ),
    }

    await query.message.reply_text(instructions[action])


_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_calculate(expression: str):
    def evaluate(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("Exponent too large.")

            return _ALLOWED_OPERATORS[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
            return _ALLOWED_OPERATORS[type(node.op)](evaluate(node.operand))

        raise ValueError("Invalid expression.")

    tree = ast.parse(expression, mode="eval")
    return evaluate(tree.body)


def convert_unit(text: str):
    parts = text.lower().replace(" to ", " ").split()

    if len(parts) != 3:
        raise ValueError("Format: 10 km to miles")

    value = float(parts[0])
    source = parts[1]
    target = parts[2]

    conversions = {
        ("km", "miles"): value * 0.621371,
        ("miles", "km"): value / 0.621371,
        ("kg", "lb"): value * 2.20462,
        ("lb", "kg"): value / 2.20462,
        ("cm", "m"): value / 100,
        ("m", "cm"): value * 100,
        ("c", "f"): (value * 9 / 5) + 32,
        ("f", "c"): (value - 32) * 5 / 9,
    }

    result = conversions.get((source, target))

    if result is None:
        raise ValueError("Unsupported conversion.")

    return result


async def utility_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.message.text:
        return

    action = context.user_data.get("utility_action")

    if not action:
        return

    text = update.message.text.strip()

    try:
        if action == "calc":
            result = safe_calculate(text)
            response = f"🧮 Result: {result}"

        elif action == "date":
            target = date.fromisoformat(text)
            difference = (target - date.today()).days
            response = (
                f"📅 Date: {target.isoformat()}\n"
                f"Days from today: {difference}"
            )

        elif action == "unit":
            result = convert_unit(text)
            response = f"📏 Converted value: {result:.4f}"

        elif action == "currency":
            response = "💱 Live currency conversion is not available yet."

        elif action == "qr":
            response = "🔳 QR generation will be connected later."

        else:
            response = "Unknown utility."

        await update.message.reply_text(response)

    except Exception:
        await update.message.reply_text(
            "❌ Could not process that input.\n"
            "Please check the format and try again."
        )

    context.user_data.pop("utility_action", None)
