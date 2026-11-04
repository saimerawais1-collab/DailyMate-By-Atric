


import asyncio
from groq import Groq

from config import GROQ_API_KEY

MODEL_NAME = "openai/gpt-oss-120b"


class AIServiceError(Exception):
    """Raised when the AI service cannot generate a response."""


def _generate_response(prompt: str) -> str:
    if not GROQ_API_KEY:
        raise AIServiceError(
            "AI service is not configured. "
            "Please contact the administrator."
        )

    client = Groq(api_key=GROQ_API_KEY)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Daily-Mate By Atric, a helpful, "
                    "friendly, accurate AI assistant. "
                    "Reply in the language the user prefers."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.7,
        max_tokens=1000,
    )

    result = response.choices[0].message.content

    if not result:
        raise AIServiceError("The AI returned an empty response.")

    return result


async def ask_ai(prompt: str) -> str:
    try:
        return await asyncio.to_thread(
            _generate_response,
            prompt,
        )
    except AIServiceError:
        raise
    except Exception as error:
        print(f"Groq API error: {error}")
        raise AIServiceError(
            "AI service is temporarily unavailable. "
            "Please try again later."
        ) from error
