"""
Voice Interface Service (Feature 10)

Provides speech-to-text (Whisper) and text-to-speech (gTTS) functionality.
"""
from __future__ import annotations

import io
import os
import tempfile
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

_whisper_model = None

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


def _get_whisper_model():
    """Lazily load the Whisper base model."""
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            _whisper_model = whisper.load_model("base")
            logger.info("Whisper base model loaded")
        except Exception as exc:
            logger.error("Failed to load Whisper model: %s", exc)
            raise
    return _whisper_model


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """
    Transcribe audio bytes to text using OpenAI Whisper.

    Supports wav, mp3, and ogg formats.
    """
    try:
        model = _get_whisper_model()
        suffix = os.path.splitext(filename)[-1] or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            result = model.transcribe(tmp_path)
            transcript = result.get("text", "").strip()
            logger.info("Transcribed %d bytes to: %s...", len(audio_bytes), transcript[:80])
            return transcript
        finally:
            os.unlink(tmp_path)

    except Exception as exc:
        logger.error("Transcription failed: %s", exc)
        raise


def text_to_speech(text: str, lang: str = "en") -> bytes:
    """
    Convert text to speech using gTTS.

    Returns MP3 bytes.
    """
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang, slow=False)
        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)
        return buffer.read()
    except Exception as exc:
        logger.error("Text-to-speech failed: %s", exc)
        raise
