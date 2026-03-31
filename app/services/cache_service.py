"""
Semantic Response Cache (Feature 5)

Uses Redis to cache RAG query results. Embeddings are compared with cosine
similarity. Cache is completely optional — all failures are silently swallowed
so that main query flow is never interrupted.
"""
from __future__ import annotations

import hashlib
import json
from typing import Optional

import numpy as np

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

CACHE_TTL = 3600  # 1 hour
SIMILARITY_THRESHOLD = 0.92
KEY_PREFIX = "miha:cache:"

# Lazily initialised Redis client
_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if not settings.redis_url:
        return None
    try:
        import redis as redis_lib

        _redis_client = redis_lib.from_url(settings.redis_url, decode_responses=True)
        _redis_client.ping()
        logger.info("Redis cache connected: %s", settings.redis_url)
        return _redis_client
    except Exception as exc:
        logger.warning("Redis unavailable — caching disabled: %s", exc)
        return None


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _embedding_hash(embedding: np.ndarray) -> str:
    """Deterministic hex digest of a float32 array."""
    raw = embedding.astype("float32").tobytes()
    return hashlib.sha256(raw).hexdigest()[:32]


def get_cached_response(query_embedding: np.ndarray) -> Optional[dict]:
    """
    Search Redis for a semantically similar cached query.

    Returns the cached payload (with 'cached': True injected) or None.
    """
    r = _get_redis()
    if r is None:
        return None
    try:
        pattern = KEY_PREFIX + "*"
        keys = r.keys(pattern)
        for key in keys:
            raw = r.get(key)
            if raw is None:
                continue
            payload = json.loads(raw)
            cached_emb = np.array(payload["embedding"], dtype="float32")
            sim = _cosine_similarity(query_embedding, cached_emb)
            if sim >= SIMILARITY_THRESHOLD:
                logger.info("Cache hit (similarity=%.4f) for key %s", sim, key)
                result = {k: v for k, v in payload.items() if k != "embedding"}
                result["cached"] = True
                return result
        return None
    except Exception as exc:
        logger.warning("Cache lookup failed: %s", exc)
        return None


def store_cached_response(
    query: str,
    query_embedding: np.ndarray,
    answer: str,
    sources: list,
) -> None:
    """Store a query result in Redis with TTL."""
    r = _get_redis()
    if r is None:
        return
    try:
        key = KEY_PREFIX + _embedding_hash(query_embedding)
        payload = {
            "query": query,
            "answer": answer,
            "sources": sources,
            "embedding": query_embedding.tolist(),
        }
        r.setex(key, CACHE_TTL, json.dumps(payload))
        logger.info("Cached response stored at key %s", key)
    except Exception as exc:
        logger.warning("Cache store failed: %s", exc)
