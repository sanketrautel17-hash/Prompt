from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.db.mongodb import connect_db, close_db
from core.apis.routers.voice import router as voice_router
from core.apis.routers.history import router as history_router
from commons.logger import logger as get_logger

log = get_logger("api")


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
# CORS — allow all origins (desktop app calls localhost)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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