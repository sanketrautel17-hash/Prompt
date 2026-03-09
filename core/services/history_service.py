"""
core/services/history_service.py
---------------------------------
MongoDB CRUD operations for saved prompts.
Uses the singleton DB connection from core.db.mongodb.
"""

from datetime import datetime, timezone
import asyncio
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException

from core.db.mongodb import get_db
from commons.logger import logger as get_logger

log = get_logger("services.history")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doc_to_dict(doc: dict) -> dict:
    """Convert a MongoDB document to a serializable dict (ObjectId → str)."""
    doc["id"] = str(doc.pop("_id"))
    return doc


def _parse_object_id(prompt_id: str) -> ObjectId:
    """Parse string to ObjectId, raise 404 on invalid format."""
    try:
        return ObjectId(prompt_id)
    except InvalidId:
        log.warning("Invalid ObjectId format received: '%s'", prompt_id)
        raise HTTPException(status_code=404, detail=f"Invalid prompt ID: '{prompt_id}'")


def _get_collection():
    """Return prompts collection or raise 503 when DB is not configured/connected."""
    try:
        db = get_db()
        return db["prompts"]
    except RuntimeError as e:
        log.error("Database unavailable: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable. Configure MONGODB_URI and restart the server.",
        ) from e


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

async def save_prompt(
    transcript: str,
    intent: str,
    framework: str,
    generated_prompt: str,
    language: str,
    processing_time_ms: int,
) -> str:
    """
    Save a generated prompt to the MongoDB 'prompts' collection.

    Returns:
        The inserted document's ObjectId as a string.

    Raises:
        HTTPException 500: If the insert fails.
    """
    collection = _get_collection()

    document = {
        "transcript": transcript,
        "intent": intent,
        "framework": framework,
        "generated_prompt": generated_prompt,
        "language": language,
        "processing_time_ms": processing_time_ms,
        "created_at": datetime.now(timezone.utc),
    }

    log.info("Saving prompt to DB | intent=%s | framework=%s | language=%s", intent, framework, language)
    try:
        result = await asyncio.to_thread(collection.insert_one, document)
        prompt_id = str(result.inserted_id)
        log.info("Prompt saved successfully | id=%s", prompt_id)
        return prompt_id
    except Exception as e:
        log.exception("Failed to save prompt to database: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save prompt to database: {str(e)}",
        ) from e


async def get_all_prompts(limit: int = 50, skip: int = 0) -> tuple[int, list[dict]]:
    """
    Fetch all saved prompts, sorted newest first.

    Args:
        limit: Max number of results (default 50).
        skip:  Number of results to skip for pagination.

    Returns:
        Tuple of (total_count, list_of_prompt_dicts).
    """
    collection = _get_collection()

    log.info("Fetching all prompts | limit=%d | skip=%d", limit, skip)
    total = await asyncio.to_thread(collection.count_documents, {})
    docs = await asyncio.to_thread(
        lambda: list(collection.find({}).sort("created_at", -1).skip(skip).limit(limit))
    )
    items = [_doc_to_dict(doc) for doc in docs]
    log.info("Fetched %d / %d prompts", len(items), total)
    return total, items


async def get_prompt_by_id(prompt_id: str) -> dict:
    """
    Fetch a single prompt by its MongoDB ObjectId.

    Raises:
        HTTPException 404: If the prompt doesn't exist.
    """
    collection = _get_collection()
    oid = _parse_object_id(prompt_id)

    log.info("Fetching prompt by id=%s", prompt_id)
    doc = await asyncio.to_thread(collection.find_one, {"_id": oid})
    if doc is None:
        log.warning("Prompt not found: id=%s", prompt_id)
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found.")

    log.info("Prompt fetched successfully | id=%s", prompt_id)
    return _doc_to_dict(doc)


async def delete_prompt(prompt_id: str) -> None:
    """
    Delete a prompt by its MongoDB ObjectId.

    Raises:
        HTTPException 404: If the prompt doesn't exist.
    """
    collection = _get_collection()
    oid = _parse_object_id(prompt_id)

    log.info("Deleting prompt | id=%s", prompt_id)
    result = await asyncio.to_thread(collection.delete_one, {"_id": oid})
    if result.deleted_count == 0:
        log.warning("Prompt not found for deletion: id=%s", prompt_id)
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found.")

    log.info("Prompt deleted successfully | id=%s", prompt_id)
