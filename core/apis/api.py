from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from core.db.mongodb import connect_db, close_db
from core.apis.routers.voice import router as voice_router
from core.apis.routers.history import router as history_router
from commons.logger import logger as get_logger

log = get_logger("api")


def _cors_origins() -> list[str]:
    """
    Parse CORS origins from env.
    - CORS_ALLOW_ORIGINS="*" (default)
    - CORS_ALLOW_ORIGINS="http://localhost:3000,https://app.example.com"
    """
    raw = os.getenv("CORS_ALLOW_ORIGINS", "*").strip()
    if not raw:
        return ["*"]
    if raw == "*":
        return ["*"]
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins or ["*"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    log.info("VoicePrompt AI starting up...")
    await connect_db()
    yield
    log.info("VoicePrompt AI shutting down...")
    await close_db()


app = FastAPI(
    title="VoicePrompt AI",
    description="Voice-to-prompt pipeline: STT → Intent → LLM → Structured Prompt",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — desktop app does not require browser credentials.
# ---------------------------------------------------------------------------
_origins = _cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=("*" not in _origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(voice_router, prefix="/voice", tags=["Voice"])
app.include_router(history_router, prefix="/history", tags=["History"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    """Returns server status. Used by the desktop app to verify connectivity."""
    return {"status": "ok", "service": "VoicePrompt AI"}
