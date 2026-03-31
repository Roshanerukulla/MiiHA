"""
Voice Interface API (Feature 10)

POST /api/v1/voice/transcribe — speech-to-text (Whisper)
POST /api/v1/voice/query      — transcribe + RAG query
GET  /api/v1/voice/speak      — text-to-speech (gTTS)
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import Response

from app.core.dependencies import get_current_user
from app.services.query_service import query_rag
from app.services.voice_service import MAX_FILE_SIZE, text_to_speech, transcribe_audio
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

_executor = ThreadPoolExecutor(max_workers=2)

ALLOWED_CONTENT_TYPES = {
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
    "application/ogg",
    "audio/webm",
}


def _validate_audio(file: UploadFile) -> None:
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio format '{file.content_type}'. "
                   f"Supported: wav, mp3, ogg",
        )


@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(..., description="Audio file (wav/mp3/ogg, max 25MB)"),
    user: dict = Depends(get_current_user),
) -> dict:
    """Transcribe an uploaded audio file to text using Whisper."""
    _validate_audio(audio)
    audio_bytes = await audio.read()
    if len(audio_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio file exceeds 25MB limit",
        )
    loop = asyncio.get_event_loop()
    transcript = await loop.run_in_executor(
        _executor,
        lambda: transcribe_audio(audio_bytes, audio.filename or "audio.wav"),
    )
    return {"transcript": transcript}


@router.post("/query")
async def voice_query(
    audio: UploadFile = File(..., description="Audio file (wav/mp3/ogg, max 25MB)"),
    user: dict = Depends(get_current_user),
) -> dict:
    """Transcribe audio and run a full RAG query, returning transcript + answer."""
    _validate_audio(audio)
    audio_bytes = await audio.read()
    if len(audio_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio file exceeds 25MB limit",
        )
    loop = asyncio.get_event_loop()
    transcript = await loop.run_in_executor(
        _executor,
        lambda: transcribe_audio(audio_bytes, audio.filename or "audio.wav"),
    )
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not transcribe audio — empty transcript",
        )
    user_profile = dict(user)
    result = await query_rag(query=transcript, user_profile=user_profile)
    return {
        "transcript": transcript,
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
        "query_id": result.get("query_id"),
    }


@router.get("/speak")
async def speak(
    text: str = Query(..., min_length=1, max_length=2000, description="Text to synthesise"),
    lang: str = Query(default="en", description="BCP 47 language code (e.g. 'en', 'es')"),
    user: dict = Depends(get_current_user),
) -> Response:
    """Convert text to speech using gTTS. Returns audio/mpeg bytes."""
    loop = asyncio.get_event_loop()
    audio_bytes = await loop.run_in_executor(
        _executor,
        lambda: text_to_speech(text, lang),
    )
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"Content-Disposition": 'inline; filename="speech.mp3"'},
    )
