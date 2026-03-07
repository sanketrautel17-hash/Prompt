"""
core/apis/routers/history.py
-----------------------------
History CRUD endpoints:
  GET    /history              — list all saved prompts (paginated)
  GET    /history/{id}         — get a single prompt by ID
  DELETE /history/{id}         — delete a prompt by ID
"""

from fastapi import APIRouter, Query

from core.services.history_service import get_all_prompts, get_prompt_by_id, delete_prompt
from core.models.prompt_model import PromptHistoryItem, PromptHistoryList


router = APIRouter()


@router.get(
    "",
    response_model=PromptHistoryList,
    summary="List all saved prompts",
    description="Returns a paginated list of all saved prompts, sorted newest first.",
)
async def list_history(
    limit: int = Query(default=50, ge=1, le=200, description="Max results to return"),
    skip: int = Query(default=0, ge=0, description="Number of results to skip (for pagination)"),
) -> PromptHistoryList:
    """
    Fetch all saved prompts from MongoDB.

    Args:
        limit: Maximum number of items to return (1–200).
        skip:  Number of items to skip for pagination.

    Returns:
        PromptHistoryList with total count and paged items.
    """
    total, items = await get_all_prompts(limit=limit, skip=skip)
    return PromptHistoryList(
        total=total,
        items=[PromptHistoryItem(**item) for item in items],
    )


@router.get(
    "/{prompt_id}",
    response_model=PromptHistoryItem,
    summary="Get a prompt by ID",
    description="Fetch a single saved prompt using its MongoDB ObjectId.",
)
async def get_one_prompt(prompt_id: str) -> PromptHistoryItem:
    """
    Retrieve a single prompt by its ObjectId string.

    Args:
        prompt_id: MongoDB ObjectId as a 24-character hex string.

    Raises:
        HTTPException 404: If the ID doesn't exist or is malformed.
    """
    doc = await get_prompt_by_id(prompt_id)
    return PromptHistoryItem(**doc)


@router.delete(
    "/{prompt_id}",
    status_code=204,
    summary="Delete a prompt by ID",
    description="Permanently delete a saved prompt from history.",
)
async def delete_one_prompt(prompt_id: str) -> None:
    """
    Delete a prompt by its ObjectId string.

    Args:
        prompt_id: MongoDB ObjectId as a 24-character hex string.

    Raises:
        HTTPException 404: If the ID doesn't exist or is malformed.
    """
    await delete_prompt(prompt_id)
