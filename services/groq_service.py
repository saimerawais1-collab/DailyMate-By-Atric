
import asyncio
from groq import Groq
from config import GROQ_API_KEY


MODEL_NAME = "llama-3.3-70b-versatile"


def _generate_response(prompt: str) -> str:
    if not GROQ_API_KEY:
        return (
            "AI service is not configured yet.\n\n"
            "The administrator needs to add the GROQ_API_KEY "
            "secret in GitHub."
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
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=1000,
    )

    return response.choices[0].message.content or "No response."


async def ask_ai(prompt: str) -> str:
    try:
        return await asyncio.to_thread(_generate_response, prompt)
    except Exception as error:
        print(f"Groq API error: {error}")
        return (
            "Sorry, AI service is temporarily unavailable. "
            "Please try again later."
        )
