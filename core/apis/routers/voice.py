"""
core/apis/routers/voice.py
--------------------------
POST /voice/process

Accepts a multipart audio file upload, runs the full pipeline:
  1. Transcribe audio → Deepgram STT
  2. Detect intent + select framework
  3. Generate structured prompt → Groq LLaMA 3.3
  4. Save result to MongoDB
  5. Return full VoiceProcessResponse
"""

import time
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, UploadFile, HTTPException

from core.services.deepgram_service import transcribe_audio
from core.services.intent_service import detect_intent
from core.services.groq_service import generate_prompt
from core.services.history_service import save_prompt
from core.models.prompt_model import Language, VoiceProcessResponse
from commons.logger import logger as get_logger

log = get_logger("routers.voice")
router = APIRouter()


@router.post(
    "/process",
    response_model=VoiceProcessResponse,
    summary="Process voice recording",
    description=(
        "Upload a WAV/WebM audio file. The pipeline will transcribe it, detect intent, "
        "generate a structured AI prompt, save it to history, and return the full result."
    ),
)
async def process_voice(
    file: UploadFile = File(..., description="Audio file (WAV or WebM)"),
    language: Language = Form(default="en", description="Language of the audio (en | hi | mr)"),
) -> VoiceProcessResponse:
    """
    Full voice → prompt pipeline endpoint.

    Steps:
        1. Read audio bytes from uploaded file
        2. Transcribe with Deepgram Nova-2
        3. Detect intent & select framework (keyword-based)
        4. Generate structured prompt with Groq LLaMA 3.3
        5. Save to MongoDB and return the response

    Raises:
        HTTPException 400: If no file is provided or file is empty.
        HTTPException 422: If Deepgram returns an empty transcript.
        HTTPException 502: If Deepgram or Groq API calls fail.
        HTTPException 500: If saving to DB fails.
    """
    start_ms = time.monotonic()
    log.info("Voice process request received | file=%s | language=%s", file.filename, language)

    # ── 1. Read audio bytes ────────────────────────────────────────────────
    audio_bytes = await file.read()
    if not audio_bytes:
        log.error("Empty audio file received | file=%s", file.filename)
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

    # ── 2. Transcribe ──────────────────────────────────────────────────────
    transcript = await transcribe_audio(audio_bytes, language=language)

    # ── 3. Detect intent & framework ───────────────────────────────────────
    intent, framework = detect_intent(transcript)
    log.info("Intent detected | intent=%s | framework=%s", intent, framework)

    # ── 4. Generate structured prompt ─────────────────────────────────────
    generated_prompt = await generate_prompt(transcript, framework=framework)

    # ── 5. Save to MongoDB ──────────────────────────────────────────────────
    elapsed_ms = int((time.monotonic() - start_ms) * 1000)
    created_at = datetime.now(timezone.utc)

    prompt_id = await save_prompt(
        transcript=transcript,
        intent=intent,
        framework=framework,
        generated_prompt=generated_prompt,
        language=language,
        processing_time_ms=elapsed_ms,
    )

    log.info(
        "Voice pipeline completed | id=%s | intent=%s | framework=%s | elapsed_ms=%d",
        prompt_id, intent, framework, elapsed_ms,
    )

    return VoiceProcessResponse(
        id=prompt_id,
        transcript=transcript,
        intent=intent,
        framework=framework,
        generated_prompt=generated_prompt,
        language=language,
        processing_time_ms=elapsed_ms,
        created_at=created_at,
    )
