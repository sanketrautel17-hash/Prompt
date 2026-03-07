"""
core/db/mongodb.py
------------------
MongoDB Atlas connection — singleton pattern.
Connect once on startup, reuse across all requests.
"""

import os
import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

from commons.logger import logger as get_logger

load_dotenv()

log = get_logger("db.mongodb")

_client: MongoClient | None = None


def get_db():
    """Return the voiceprompt database. Raises RuntimeError if not connected."""
    if _client is None:
        raise RuntimeError("MongoDB client is not initialized. Call connect_db() first.")
    return _client[os.getenv("MONGODB_DB_NAME", "voiceprompt")]


async def connect_db() -> None:
    """
    Initialize the MongoDB client and verify connectivity with a ping.
    Called during FastAPI lifespan startup.
    A failed connection logs a warning but does NOT crash the server —
    errors surface only when a DB operation is actually attempted.
    """
    global _client
    uri = os.getenv("MONGODB_URI")
    if not uri:
        log.warning("MONGODB_URI not set — skipping connection.")
        return

    log.info("Connecting to MongoDB Atlas...")
    # tlsCAFile=certifi.where() fixes SSL handshake errors on Windows
    # by using certifi's trusted CA bundle instead of the system store.
    _client = MongoClient(
        uri,
        serverSelectionTimeoutMS=5000,
        tlsCAFile=certifi.where(),
    )

    # Ping to confirm connection
    try:
        _client.admin.command("ping")
        db_name = os.getenv("MONGODB_DB_NAME", "voiceprompt")
        log.info("Connected to MongoDB Atlas — database: '%s'", db_name)
    except ConnectionFailure as e:
        log.error("Could not reach MongoDB Atlas: %s", e)
        log.warning("Server will start anyway. Check your Atlas Network Access if this persists.")
        # Keep _client set so reconnect is possible


async def close_db() -> None:
    """
    Close the MongoDB client.
    Called during FastAPI lifespan shutdown.
    """
    global _client
    if _client is not None:
        _client.close()
        _client = None
        log.info("MongoDB connection closed.")
