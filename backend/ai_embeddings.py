from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable

import httpx
from sqlalchemy.orm import Session

from config import settings
import models


logger = logging.getLogger(__name__)

CHUNK_MAX_CHARS = 1_100
CHUNK_OVERLAP_CHARS = 180
LOCAL_EMBEDDING_DIM = 256
MAX_QUERY_CANDIDATES = 2_000
_TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9_]{2,}")


@dataclass
class ContextSource:
    user_id: int
    scope: str
    entity_type: str
    entity_id: str | int
    title: str
    text: str
    parent_type: str = ""
    parent_id: str | int = ""
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def source_key(self) -> str:
        parent = f"{self.parent_type}:{self.parent_id}" if self.parent_type and self.parent_id != "" else "root"
        return f"{self.scope}:{parent}:{self.entity_type}:{self.entity_id}"


@dataclass
class SemanticHit:
    title: str
    text: str
    score: float
    scope: str
    entity_type: str
    entity_id: str
    parent_type: str
    parent_id: str
    metadata: dict[str, object]


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _source_hash(source: ContextSource) -> str:
    payload = {
        "title": source.title,
        "text": _normalize_text(source.text),
        "metadata": source.metadata,
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def chunk_text(text: str, *, max_chars: int = CHUNK_MAX_CHARS, overlap_chars: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    clean = _normalize_text(text)
    if not clean:
        return []
    if len(clean) <= max_chars:
        return [clean]

    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(len(clean), start + max_chars)
        if end < len(clean):
            split_at = max(clean.rfind(". ", start, end), clean.rfind("; ", start, end), clean.rfind(" ", start, end))
            if split_at > start + max_chars // 2:
                end = split_at + 1
        chunk = clean[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(clean):
            break
        start = max(0, end - overlap_chars)
    return chunks


def _local_embedding(text: str, *, dim: int = LOCAL_EMBEDDING_DIM) -> list[float]:
    vector = [0.0] * dim
    tokens = [token.casefold().strip("_") for token in _TOKEN_RE.findall(text or "")]
    for token in tokens:
        if len(token) < 3:
            continue
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 0:
        return vector
    return [value / norm for value in vector]


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def _api_embeddings(texts: list[str]) -> list[list[float]] | None:
    model = settings.routerai_embedding_model.strip()
    if not model:
        return None

    api_key = settings.routerai_api_key.strip()
    if not api_key:
        return None

    url = f"{settings.routerai_base_url.rstrip('/')}/embeddings"
    payload = {"model": model, "input": texts}
    try:
        with httpx.Client(timeout=settings.routerai_timeout_sec) as client:
            resp = client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
            )
        if not resp.is_success:
            logger.warning("Embeddings API returned %s: %s", resp.status_code, resp.text[:240])
            return None
        data = resp.json()
        rows = sorted(data.get("data", []), key=lambda item: item.get("index", 0))
        embeddings = [item.get("embedding") for item in rows]
        if len(embeddings) != len(texts) or not all(isinstance(item, list) for item in embeddings):
            logger.warning("Embeddings API returned unexpected payload")
            return None
        return embeddings
    except Exception as exc:  # pragma: no cover
        logger.warning("Embeddings API failed, using local fallback: %s", exc)
        return None


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    api_values = _api_embeddings(texts)
    if api_values is not None:
        return api_values
    return [_local_embedding(text) for text in texts]


def _json_vector(value: str) -> list[float]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [float(item) for item in parsed if isinstance(item, (int, float))]


def ensure_context_sources_indexed(db: Session, sources: Iterable[ContextSource]) -> None:
    if not settings.ai_embeddings_enabled:
        return

    changed_sources: list[tuple[ContextSource, str, list[str]]] = []
    for source in sources:
        text = _normalize_text(source.text)
        source_hash = _source_hash(source)
        existing = (
            db.query(models.AiContextChunk.id)
            .filter(
                models.AiContextChunk.user_id == source.user_id,
                models.AiContextChunk.source_key == source.source_key,
                models.AiContextChunk.source_hash == source_hash,
            )
            .first()
        )
        if existing:
            continue

        db.query(models.AiContextChunk).filter(
            models.AiContextChunk.user_id == source.user_id,
            models.AiContextChunk.source_key == source.source_key,
        ).delete(synchronize_session=False)

        chunks = chunk_text(text)
        if chunks:
            changed_sources.append((source, source_hash, chunks))

    if not changed_sources:
        return

    texts_to_embed: list[str] = []
    owners: list[tuple[ContextSource, str, int, str]] = []
    for source, source_hash, chunks in changed_sources:
        for index, chunk in enumerate(chunks):
            texts_to_embed.append(f"{source.title}\n{chunk}")
            owners.append((source, source_hash, index, chunk))

    vectors = embed_texts(texts_to_embed)
    now = datetime.utcnow()
    for (source, source_hash, index, chunk), vector in zip(owners, vectors):
        db.add(
            models.AiContextChunk(
                user_id=source.user_id,
                scope=source.scope,
                entity_type=source.entity_type,
                entity_id=str(source.entity_id),
                parent_type=source.parent_type,
                parent_id=str(source.parent_id) if source.parent_id != "" else "",
                source_key=source.source_key,
                source_hash=source_hash,
                chunk_index=index,
                title=source.title[:400],
                text=chunk,
                metadata_json=json.dumps(source.metadata, ensure_ascii=False, sort_keys=True),
                embedding_json=json.dumps(vector, ensure_ascii=False),
                created_at=now,
                updated_at=now,
            )
        )

    db.commit()


def prune_stale_context_sources(
    db: Session,
    *,
    user_id: int,
    sources: Iterable[ContextSource],
    scopes: set[str] | None = None,
    parent_type: str | None = None,
    parent_id: str | int | None = None,
) -> None:
    if not settings.ai_embeddings_enabled:
        return

    current_keys = {source.source_key for source in sources}
    query = db.query(models.AiContextChunk).filter(models.AiContextChunk.user_id == user_id)
    if scopes:
        query = query.filter(models.AiContextChunk.scope.in_(sorted(scopes)))
    if parent_type is not None:
        query = query.filter(models.AiContextChunk.parent_type == parent_type)
    if parent_id is not None:
        query = query.filter(models.AiContextChunk.parent_id == str(parent_id))

    if current_keys:
        query = query.filter(~models.AiContextChunk.source_key.in_(sorted(current_keys)))

    deleted = query.delete(synchronize_session=False)
    if deleted:
        db.commit()


def delete_context_chunks(
    db: Session,
    *,
    user_id: int | None = None,
    scope: str | None = None,
    entity_type: str | None = None,
    entity_id: str | int | None = None,
    parent_type: str | None = None,
    parent_id: str | int | None = None,
) -> int:
    query = db.query(models.AiContextChunk)
    if user_id is not None:
        query = query.filter(models.AiContextChunk.user_id == user_id)
    if scope is not None:
        query = query.filter(models.AiContextChunk.scope == scope)
    if entity_type is not None:
        query = query.filter(models.AiContextChunk.entity_type == entity_type)
    if entity_id is not None:
        query = query.filter(models.AiContextChunk.entity_id == str(entity_id))
    if parent_type is not None:
        query = query.filter(models.AiContextChunk.parent_type == parent_type)
    if parent_id is not None:
        query = query.filter(models.AiContextChunk.parent_id == str(parent_id))
    return query.delete(synchronize_session=False)


def semantic_search_context(
    db: Session,
    *,
    user_id: int,
    query: str,
    scopes: set[str] | None = None,
    parent_type: str | None = None,
    parent_id: str | int | None = None,
    entity_types: set[str] | None = None,
    limit: int = 6,
    min_score: float = 0.12,
) -> list[SemanticHit]:
    if not settings.ai_embeddings_enabled or not query.strip():
        return []

    query_vector = embed_texts([query])[0]
    rows_query = db.query(models.AiContextChunk).filter(models.AiContextChunk.user_id == user_id)
    if scopes:
        rows_query = rows_query.filter(models.AiContextChunk.scope.in_(sorted(scopes)))
    if parent_type is not None:
        rows_query = rows_query.filter(models.AiContextChunk.parent_type == parent_type)
    if parent_id is not None:
        rows_query = rows_query.filter(models.AiContextChunk.parent_id == str(parent_id))
    if entity_types:
        rows_query = rows_query.filter(models.AiContextChunk.entity_type.in_(sorted(entity_types)))

    rows = rows_query.order_by(models.AiContextChunk.updated_at.desc()).limit(MAX_QUERY_CANDIDATES).all()

    scored: list[tuple[float, models.AiContextChunk]] = []
    for row in rows:
        score = _cosine(query_vector, _json_vector(row.embedding_json))
        if score >= min_score:
            scored.append((score, row))

    scored.sort(key=lambda item: item[0], reverse=True)

    hits: list[SemanticHit] = []
    seen_sources: set[str] = set()
    for score, row in scored:
        source_marker = f"{row.source_key}:{row.chunk_index}"
        if source_marker in seen_sources:
            continue
        seen_sources.add(source_marker)
        try:
            metadata = json.loads(row.metadata_json or "{}")
        except json.JSONDecodeError:
            metadata = {}
        hits.append(
            SemanticHit(
                title=row.title,
                text=row.text,
                score=score,
                scope=row.scope,
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                parent_type=row.parent_type,
                parent_id=row.parent_id,
                metadata=metadata if isinstance(metadata, dict) else {},
            )
        )
        if len(hits) >= limit:
            break
    return hits


def render_semantic_hits(hits: list[SemanticHit], *, max_chars_per_hit: int = 900) -> str:
    if not hits:
        return ""

    lines: list[str] = []
    for hit in hits:
        score = f"{hit.score:.2f}"
        text = hit.text
        if len(text) > max_chars_per_hit:
            text = text[: max_chars_per_hit - 28].rstrip() + "\n...[semantic excerpt clipped]"
        lines.append(f"- {hit.title} (score {score}):\n{text}")
    return "\n\n".join(lines)
