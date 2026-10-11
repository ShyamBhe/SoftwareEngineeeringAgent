import json
import re

from google import genai
from google.genai import types

from .config import settings

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _strip_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())


def ask(system: str, user: str, max_tokens: int = 8000) -> str:
    response = _get_client().models.generate_content(
        model=settings.agent_model,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return response.text


def ask_json(system: str, user: str, max_tokens: int = 8000):
    json_system = (
        system
        + "\nReturn ONLY valid JSON. No markdown fences, no commentary."
    )

    raw = _strip_fences(ask(json_system, user, max_tokens))

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        fixed = ask(
            "Repair this into valid JSON. Return only the JSON.",
            raw,
            max_tokens,
        )
        return json.loads(_strip_fences(fixed))