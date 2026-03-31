"""Cohere-based reranking for combined MedlinePlus + OpenFDA results."""

import cohere

from app.config.llmconfig import COHERE_RERANK_MODEL
from app.utils.logger import get_logger

logger = get_logger(__name__)


def rerank_with_cohere(
    co: cohere.Client,
    query: str,
    raw_chunks: list,
    top_n: int = 3,
) -> list:
    """
    Rerank raw retrieval chunks using Cohere's rerank API.

    Falls back to the first `top_n` raw chunks if no usable text is found
    or if the rerank call fails.
    """
    documents = []
    for doc in raw_chunks:
        if doc.get("source") == "MedlinePlus":
            text = (doc.get("title") or "").strip()
        else:
            text = (doc.get("purpose") or doc.get("drug_name") or "").strip()
        documents.append(text)

    # Keep only non-empty entries (preserve original index for remapping)
    non_empty = [(i, d) for i, d in enumerate(documents) if d]
    if not non_empty:
        logger.warning("Reranker: no usable document text found; returning top raw chunks")
        return raw_chunks[:top_n]

    original_indices, doc_texts = zip(*non_empty)

    results = co.rerank(
        query=query,
        documents=list(doc_texts),
        top_n=min(top_n, len(doc_texts)),
        model=COHERE_RERANK_MODEL,
    ).results

    reranked = [raw_chunks[original_indices[r.index]] for r in results]
    logger.info(f"Reranker: returned {len(reranked)} chunks from {len(raw_chunks)} candidates")
    return reranked
