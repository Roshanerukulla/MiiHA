"""Cohere-based answer generation for MIIHA."""

import cohere

from app.config.llmconfig import COHERE_GENERATE_MODEL, MAX_TOKENS, TEMPERATURE
from app.rag.prompt_engine import build_prompt
from app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_answer(co: cohere.Client, query: str, context_docs: list) -> str:
    """
    Generate a grounded medical answer via Cohere's generate API.

    Args:
        co: Initialised Cohere client.
        query: The user's health question.
        context_docs: Reranked source documents to ground the answer.

    Returns:
        The generated answer string.
    """
    prompt = build_prompt(query, context_docs)

    response = co.generate(
        model=COHERE_GENERATE_MODEL,
        prompt=prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )

    answer = response.generations[0].text.strip()
    logger.info(f"Generator: produced {len(answer)} character answer")
    return answer
