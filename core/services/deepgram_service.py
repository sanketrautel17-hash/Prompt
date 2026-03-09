"""
core/services/deepgram_service.py
----------------------------------
Speech-to-Text using Deepgram Nova-2 (SDK v6).
Features: smart_format, punctuate, filler_words suppression.
Audio is processed in memory — never written to disk.
"""

import os
from deepgram import AsyncDeepgramClient
from fastapi import HTTPException

from commons.logger import logger as get_logger

log = get_logger("services.deepgram")


async def transcribe_audio(audio_bytes: bytes, language: str = "en") -> str:
    """
    Transcribe raw audio bytes to text using Deepgram Nova-2 (SDK v6).

    Uses the new SDK v6 API:
        client.listen.v1.media.transcribe_file(request=bytes, model=..., ...)

    Args:
        audio_bytes: Raw WAV/WebM audio bytes captured from the microphone.
        language:    BCP-47 language code (en | hi | mr).

    Returns:
        Transcript string from Deepgram.

    Raises:
        HTTPException 500: If DEEPGRAM_API_KEY is missing.
        HTTPException 422: If Deepgram returns an empty transcript.
        HTTPException 502: If the Deepgram API call fails.
    """
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        log.error("DEEPGRAM_API_KEY is not set in environment variables.")
        raise HTTPException(status_code=500, detail="DEEPGRAM_API_KEY is not configured.")

    log.info("Starting transcription | language=%s | audio_size=%d bytes", language, len(audio_bytes))

    try:
        client = AsyncDeepgramClient(api_key=api_key)

        model_name = "nova-3" if language == "mr" else "nova-2"

        response = await client.listen.v1.media.transcribe_file(
            request=audio_bytes,
            model=model_name,
            language=language,
            smart_format=True,
            punctuate=True,
            filler_words=False,
        )

        # SDK v6 response: response.results.channels[0].alternatives[0].transcript
        transcript: str = (
            response.results.channels[0].alternatives[0].transcript
        )

        if not transcript.strip():
            log.warning("Deepgram returned an empty transcript for language=%s", language)
            raise HTTPException(
                status_code=422,
                detail="Deepgram returned an empty transcript. Please speak clearly and try again.",
            )

        log.info("Transcription successful | chars=%d", len(transcript.strip()))
        return transcript.strip()

    except HTTPException:
        raise
    except Exception as e:
        log.exception("Deepgram transcription failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail=f"Deepgram transcription failed: {str(e)}",
        ) from e
