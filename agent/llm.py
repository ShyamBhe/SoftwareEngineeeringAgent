import json
import re

from anthropic import Anthropic

from .config import settings

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


def _strip_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())


def ask(system: str, user: str, max_tokens: int = 8000) -> str:
    r = _get_client().messages.create(
        model=settings.agent_model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in r.content if b.type == "text")


def ask_json(system: str, user: str, max_tokens: int = 8000):
    raw = ask(system + "\nReturn ONLY valid JSON. No markdown fences, no commentary.", user, max_tokens)
    raw = _strip_fences(raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        fixed = ask("Repair this into valid JSON. Return only the JSON.", raw, max_tokens)
        return json.loads(_strip_fences(fixed))
