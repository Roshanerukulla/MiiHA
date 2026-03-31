"""
RAG query service — lazy-loads heavy resources on first use,
offloads CPU-bound work to a thread pool so the FastAPI event
loop is never blocked.
"""

import asyncio
import json
from typing import Optional

import cohere
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.config.llmconfig import SENTENCE_TRANSFORMER_MODEL, RERANK_TOP_N
from app.config.paths import (
    MEDLINE_INDEX_PATH,
    MEDLINE_METADATA_PATH,
    OPENFDA_INDEX_PATH,
    OPENFDA_METADATA_PATH,
)
from app.core.config import settings
from app.rag.generator import generate_answer
from app.rag.reranker import rerank_with_cohere
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Lazy-loaded singletons (populated on first query, not at import time)
# ---------------------------------------------------------------------------
_co: Optional[cohere.Client] = None
_model: Optional[SentenceTransformer] = None
_medline_index = None
_openfda_index = None
_medline_metadata: Optional[list] = None
_openfda_metadata: Optional[list] = None


def _get_cohere_client() -> cohere.Client:
    global _co
    if _co is None:
        _co = cohere.Client(settings.cohere_api_key)
        logger.info("Cohere client initialised")
    return _co


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading SentenceTransformer model: {SENTENCE_TRANSFORMER_MODEL}")
        _model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
        logger.info("SentenceTransformer model loaded")
    return _model


def _load_indexes() -> None:
    global _medline_index, _openfda_index, _medline_metadata, _openfda_metadata
    if _medline_index is not None:
        return  # already loaded

    for path in (MEDLINE_INDEX_PATH, OPENFDA_INDEX_PATH, MEDLINE_METADATA_PATH, OPENFDA_METADATA_PATH):
        if not path.exists():
            raise FileNotFoundError(f"Required data file not found: {path}")

    logger.info("Loading FAISS indexes and metadata…")
    _medline_index = faiss.read_index(str(MEDLINE_INDEX_PATH))
    _openfda_index = faiss.read_index(str(OPENFDA_INDEX_PATH))

    with open(MEDLINE_METADATA_PATH, "r", encoding="utf-8") as f:
        _medline_metadata = json.load(f)
    with open(OPENFDA_METADATA_PATH, "r", encoding="utf-8") as f:
        _openfda_metadata = json.load(f)

    logger.info(
        f"Loaded {len(_medline_metadata)} MedlinePlus records "
        f"and {len(_openfda_metadata)} OpenFDA records"
    )


# ---------------------------------------------------------------------------
# Core synchronous pipeline (runs inside asyncio.to_thread)
# ---------------------------------------------------------------------------

def _query_rag_sync(query: str, top_k: int) -> dict:
    _load_indexes()
    model = _get_model()
    co = _get_cohere_client()

    # 1. Embed query
    try:
        query_vector = model.encode([query])[0].astype("float32")
    except Exception as exc:
        logger.error(f"Embedding failed: {exc}")
        raise RuntimeError("Failed to embed query") from exc

    # 2. Vector search
    try:
        _, medline_indices = _medline_index.search(np.array([query_vector]), top_k)
        _, openfda_indices = _openfda_index.search(np.array([query_vector]), top_k)
    except Exception as exc:
        logger.error(f"FAISS search failed: {exc}")
        raise RuntimeError("Vector search failed") from exc

    # 3. Collect candidates
    combined_chunks = []
    for i in medline_indices[0]:
        if 0 <= i < len(_medline_metadata):
            combined_chunks.append({**_medline_metadata[i], "source": "MedlinePlus"})
    for i in openfda_indices[0]:
        if 0 <= i < len(_openfda_metadata):
            combined_chunks.append({**_openfda_metadata[i], "source": "OpenFDA"})

    if not combined_chunks:
        logger.warning(f"No retrieval results for query: {query[:80]!r}")
        return {
            "query": query,
            "answer": "I could not find relevant information to answer your question.",
            "sources": [],
        }

    # 4. Rerank — graceful fallback on failure
    try:
        reranked = rerank_with_cohere(co, query, combined_chunks, top_n=RERANK_TOP_N)
    except Exception as exc:
        logger.warning(f"Reranking failed, using top raw results: {exc}")
        reranked = combined_chunks[:RERANK_TOP_N]

    # 5. Generate answer
    try:
        answer = generate_answer(co, query, reranked)
    except Exception as exc:
        logger.error(f"Answer generation failed: {exc}")
        raise RuntimeError("Failed to generate answer") from exc

    return {"query": query, "answer": answer, "sources": reranked}


# ---------------------------------------------------------------------------
# Public async entry-point
# ---------------------------------------------------------------------------

async def query_rag(query: str, top_k: int = 15) -> dict:
    """Async wrapper — offloads the CPU-bound RAG pipeline to a thread pool."""
    return await asyncio.to_thread(_query_rag_sync, query, top_k)
