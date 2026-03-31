"""
Multi-language Support (Feature 13)

Detects the language of a query and, if not English, translates to English
before RAG and back to the original language after. Uses langdetect for
detection and Cohere generate for translation.
"""
from __future__ import annotations

from typing import Optional, Tuple

import cohere

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_co: Optional[cohere.Client] = None


def _get_client() -> cohere.Client:
    global _co
    if _co is None:
        _co = cohere.Client(settings.cohere_api_key)
    return _co


def detect_language(text: str) -> str:
    """Return ISO 639-1 language code, or 'en' on failure."""
    try:
        from langdetect import detect
        lang = detect(text)
        return lang
    except Exception as exc:
        logger.warning("Language detection failed: %s", exc)
        return "en"


def _cohere_translate(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text between languages using Cohere generate."""
    co = _get_client()
    prompt = (
        f"Translate the following text from {source_lang} to {target_lang}. "
        "Output only the translated text with no additional commentary.\n\n"
        f"Text: {text}\n\nTranslation:"
    )
    try:
        response = co.generate(
            model="command-r-plus",
            prompt=prompt,
            max_tokens=500,
            temperature=0.3,
        )
        return response.generations[0].text.strip()
    except Exception as exc:
        logger.error("Cohere translation failed: %s", exc)
        return text  # Fall back to original text


def prepare_query(query: str) -> Tuple[str, str, bool]:
    """
    Detect language and translate query to English if needed.

    Returns (english_query, detected_lang, was_translated).
    """
    lang = detect_language(query)
    if lang == "en":
        return query, lang, False
    logger.info("Query language detected: %s — translating to English", lang)
    translated = _cohere_translate(query, lang, "English")
    return translated, lang, True


def translate_answer(answer: str, target_lang: str) -> str:
    """Translate answer from English back to target_lang."""
    if target_lang == "en":
        return answer
    try:
        return _cohere_translate(answer, "English", target_lang)
    except Exception as exc:
        logger.warning("Answer translation failed: %s", exc)
        return answer
