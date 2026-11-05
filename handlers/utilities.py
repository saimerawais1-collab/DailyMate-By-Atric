

import ast
import math
import operator
import re
from datetime import date
from io import BytesIO

import httpx
import qrcode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import get_today


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


async def utilities_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "🧰 Daily Utilities\n\nSelect a tool:",
        reply_markup=utilities_menu(),
    )


async def utility_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            "💱 Currency Converter\n\n"
            "Send an amount and two currency codes:\n\n"
            "100 USD to PKR\n"
            "50 EUR to USD\n"
            "1000 PKR to SAR\n\n"
            "Rates are reference rates and may not reflect "
            "the exact rate offered by your bank or exchange."
        ),
        "qr": (
            "🔳 Send the text, link, or information "
            "you want inside your QR code."
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

            result = _ALLOWED_OPERATORS[type(node.op)](left, right)

            if isinstance(result, (int, float)):
                if not math.isfinite(result) or abs(result) > 1e100:
                    raise ValueError("Result too large.")

            return result

        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
            return _ALLOWED_OPERATORS[type(node.op)](evaluate(node.operand))

        raise ValueError("Invalid expression.")

    if len(expression) > 100:
        raise ValueError("Expression too long.")

    tree = ast.parse(expression, mode="eval")
    return evaluate(tree.body)


def convert_unit(text: str):
    parts = text.lower().replace(" to ", " ").split()

    if len(parts) != 3:
        raise ValueError("Format: 10 km to miles")

    value = float(parts[0])

    if not math.isfinite(value):
        raise ValueError("Invalid number.")

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


async def convert_currency(text: str):
    match = re.fullmatch(
        r"\s*(\d+(?:\.\d+)?)\s+([A-Za-z]{3})\s+to\s+([A-Za-z]{3})\s*",
        text,
        re.IGNORECASE,
    )

    if not match:
        raise ValueError("Format: 100 USD to PKR")

    amount = float(match.group(1))
    base = match.group(2).upper()
    quote = match.group(3).upper()

    if not math.isfinite(amount) or amount <= 0:
        raise ValueError("Enter a valid positive amount.")

    if base == quote:
        return (
            f"💱 Currency Conversion\n\n"
            f"{amount:,.2f} {base} = {amount:,.2f} {quote}\n"
            f"Exchange rate: 1 {base} = 1 {quote}\n"
            f"Rate date: Same currency"
        )

    url = f"https://api.frankfurter.dev/v2/rate/{base}/{quote}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

    rate = float(data["rate"])
    rate_date = data["date"]
    converted = amount * rate

    if not math.isfinite(rate) or rate <= 0:
        raise ValueError("Invalid exchange rate.")

    return (
        f"💱 Currency Conversion\n\n"
        f"{amount:,.2f} {base} = {converted:,.2f} {quote}\n\n"
        f"Exchange rate: 1 {base} = {rate:,.6f} {quote}\n"
        f"Rate date: {rate_date}\n\n"
        "Source: Frankfurter reference exchange rates.\n"
        "Actual bank or exchange rates may differ."
    )


def create_qr_code(content: str):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(content)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")

    output = BytesIO()
    output.name = "daily_mate_qr.png"
    image.save(output, format="PNG")
    output.seek(0)

    return output


async def utility_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    action = context.user_data.get("utility_action")

    if not action:
        return

    user_input = update.message.text.strip()

    if not user_input:
        await update.message.reply_text("Please send some text.")
        return

    try:
        if action == "calc":
            result = safe_calculate(user_input)
            await update.message.reply_text(f"🧮 Result: {result}")

        elif action == "date":
            target = date.fromisoformat(user_input)
            today = date.fromisoformat(get_today())
            difference = (target - today).days

            await update.message.reply_text(
                f"📅 Date: {target.isoformat()}\n"
                f"Days from today: {difference}"
            )

        elif action == "unit":
            result = convert_unit(user_input)
            await update.message.reply_text(
                f"📏 Converted value: {result:.4f}"
            )

        elif action == "qr":
            if len(user_input) > 2000:
                await update.message.reply_text(
                    "❌ QR content is too long. Please keep it under 2,000 characters."
                )
                return

            qr_image = create_qr_code(user_input)

            await update.message.reply_photo(
                photo=qr_image,
                caption="✅ Your QR code is ready!\nGenerated by Daily-Mate By Atric.",
            )

        elif action == "currency":
            result = await convert_currency(user_input)
            await update.message.reply_text(result)

        else:
            await update.message.reply_text("Unknown utility.")

    except httpx.HTTPStatusError:
        await update.message.reply_text(
            "❌ Currency pair not found or rate unavailable.\n"
            "Check the currency codes and try again."
        )

    except httpx.RequestError:
        await update.message.reply_text(
            "❌ Could not connect to the exchange-rate service.\n"
            "Please try again later."
        )

    except (ValueError, SyntaxError, ZeroDivisionError, OverflowError):
        await update.message.reply_text(
            "❌ Could not process that input.\n"
            "Please check the format and try again."
        )

    except Exception:
        await update.message.reply_text(
            "❌ Something went wrong while processing your request."
        )

    context.user_data.pop("utility_action", None)
