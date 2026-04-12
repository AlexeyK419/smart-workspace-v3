"""
RouterAI smoke test.
Run: python test.py
"""

import os
import asyncio

import httpx
from dotenv import load_dotenv


def get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


async def main() -> None:
    load_dotenv()

    api_key = get_env("ROUTERAI_API_KEY")
    base_url = get_env("ROUTERAI_BASE_URL", "https://routerai.ru/api/v1").rstrip("/")
    model = get_env("ROUTERAI_MODEL", "google/gemma-4-31b-it")
    timeout_raw = get_env("ROUTERAI_TIMEOUT_SEC", "60")

    try:
        timeout_sec = int(timeout_raw)
    except ValueError:
        print(f"ERROR: ROUTERAI_TIMEOUT_SEC must be integer, got: {timeout_raw}")
        return

    if not api_key:
        print("ERROR: ROUTERAI_API_KEY is not set in environment")
        return

    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a concise assistant."},
            {"role": "user", "content": "Reply with one short sentence in Russian."},
        ],
        "temperature": 0.2,
        "max_tokens": 64,
        "stream": False,
    }

    print("RouterAI smoke test started...")
    print(f"Endpoint: {url}")
    print(f"Model: {model}")

    try:
        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
            )
    except httpx.TimeoutException:
        print("ERROR: request timed out")
        return
    except httpx.RequestError as exc:
        print(f"ERROR: request failed: {exc}")
        return

    if not resp.is_success:
        detail = resp.text
        if len(detail) > 400:
            detail = detail[:400] + "..."
        print(f"ERROR: RouterAI {resp.status_code}: {detail}")
        return

    try:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        print("ERROR: unexpected response format")
        print(resp.text[:400])
        return

    text = content.strip() if isinstance(content, str) else str(content)
    preview = text[:160] + ("..." if len(text) > 160 else "")
    print("OK: smoke test passed")
    print(f"Reply: {preview}")


if __name__ == "__main__":
    asyncio.run(main())
