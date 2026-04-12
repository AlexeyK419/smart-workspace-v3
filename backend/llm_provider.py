"""
Universal LLM provider integration (RouterAI backend).
"""

import logging

import httpx

from config import settings

logger = logging.getLogger("llm_provider")


class Message:
    __slots__ = ("role", "content")

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _ensure_api_key() -> str:
    api_key = settings.routerai_api_key.strip()
    if not api_key:
        raise RuntimeError("ROUTERAI_API_KEY is not set")
    return api_key


async def chat_complete(
    messages: list[Message],
    *,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """
    Send chat completion request to RouterAI and return assistant text response.
    """
    api_key = _ensure_api_key()
    payload = {
        "model": settings.routerai_model,
        "messages": [m.to_dict() for m in messages],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    url = f"{_normalize_base_url(settings.routerai_base_url)}/chat/completions"

    try:
        async with httpx.AsyncClient(timeout=settings.routerai_timeout_sec) as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
            )
    except httpx.TimeoutException as exc:
        raise RuntimeError("RouterAI request timed out") from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"RouterAI request failed: {exc}") from exc

    if not resp.is_success:
        detail = resp.text
        if len(detail) > 400:
            detail = detail[:400] + "..."
        raise RuntimeError(f"RouterAI error {resp.status_code}: {detail}")

    try:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        logger.debug("Invalid RouterAI response payload: %s", resp.text)
        raise RuntimeError("RouterAI returned an unexpected response format") from exc

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("RouterAI returned empty response content")
    return content


async def list_models() -> list[dict]:
    """
    Return compatible model list without relying on undocumented provider endpoints.
    """
    model_id = settings.routerai_model
    return [
        {
            "id": model_id,
            "object": "model",
            "owned_by": "routerai",
        }
    ]
