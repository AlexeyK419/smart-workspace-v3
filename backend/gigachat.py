"""
GigaChat LLM Service
"""
import time
import uuid
import logging
import warnings

import httpx

from config import settings

warnings.filterwarnings("ignore")
logger = logging.getLogger("gigachat")


class _TokenCache:
    def __init__(self):
        self.access_token: str = ""
        self.expires_at: float = 0.0

    def is_valid(self) -> bool:
        return bool(self.access_token) and time.time() < (self.expires_at - 60)

    def invalidate(self):
        self.access_token = ""
        self.expires_at = 0.0


_cache = _TokenCache()


def _get_auth_key() -> str:
    """Получить Authorization Key из настроек"""
    # Пробуем разные варианты названия
    auth_key = getattr(settings, 'gigachat_auth_key', '').strip()
    if auth_key:
        return auth_key
    
    # Fallback на client_id если он похож на готовый ключ (длинная строка)
    client_id = getattr(settings, 'gigachat_client_id', '').strip()
    if client_id and len(client_id) > 50:
        return client_id
    
    raise RuntimeError(
        "GigaChat: GIGACHAT_AUTH_KEY не задан!\n"
        "Укажите в .env: GIGACHAT_AUTH_KEY=ваш_ключ_из_личного_кабинета"
    )


async def _fetch_token() -> str:
    """Получить access_token используя Authorization Key"""
    auth_key = _get_auth_key()
    rq_uid = str(uuid.uuid4())

    logger.info("Requesting GigaChat token...")
    logger.debug("RqUID: %s", rq_uid)

    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        resp = await client.post(
            settings.gigachat_auth_url,
            headers={
                # ⚠️ ВАЖНО: Bearer, не Basic!
                "Authorization": f"Bearer {auth_key}",
                "RqUID": rq_uid,
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            # ⚠️ ВАЖНО: только scope, без grant_type!
            data={"scope": settings.gigachat_scope},
        )

    if not resp.is_success:
        logger.error("Auth failed %d: %s", resp.status_code, resp.text)
        raise RuntimeError(f"GigaChat auth error: {resp.status_code} - {resp.text}")

    data = resp.json()
    _cache.access_token = data["access_token"]
    
    # expires_at в миллисекундах или expires_in в секундах
    if "expires_at" in data:
        raw_exp = data["expires_at"]
        _cache.expires_at = raw_exp / 1000 if raw_exp > 1e10 else raw_exp
    elif "expires_in" in data:
        _cache.expires_at = time.time() + data["expires_in"]
    else:
        _cache.expires_at = time.time() + 1800  # 30 минут по умолчанию

    logger.info("✅ Token obtained, expires in %.0f min", (_cache.expires_at - time.time()) / 60)
    return _cache.access_token


async def get_token() -> str:
    if _cache.is_valid():
        logger.debug("Using cached token")
        return _cache.access_token
    return await _fetch_token()


class Message:
    __slots__ = ("role", "content")

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


async def chat_complete(
    messages: list[Message],
    *,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """Отправить запрос в GigaChat и получить ответ"""
    token = await get_token()

    payload = {
        "model": settings.gigachat_model,
        "messages": [m.to_dict() for m in messages],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    logger.debug("Sending chat request to GigaChat...")

    async with httpx.AsyncClient(verify=False, timeout=60) as client:
        resp = await client.post(
            f"{settings.gigachat_api_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
        )

    # Если токен истёк — обновляем и повторяем
    if resp.status_code == 401:
        logger.warning("Token expired, refreshing...")
        _cache.invalidate()
        token = await _fetch_token()
        
        async with httpx.AsyncClient(verify=False, timeout=60) as client:
            resp = await client.post(
                f"{settings.gigachat_api_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
            )

    if not resp.is_success:
        logger.error("Chat error %d: %s", resp.status_code, resp.text)
        resp.raise_for_status()

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    logger.debug("Got response: %s...", content[:100])
    
    return content


async def list_models() -> list[dict]:
    """Получить список доступных моделей"""
    token = await get_token()
    
    async with httpx.AsyncClient(verify=False, timeout=15) as client:
        resp = await client.get(
            f"{settings.gigachat_api_url}/models",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
        )
    
    resp.raise_for_status()
    return resp.json().get("data", [])