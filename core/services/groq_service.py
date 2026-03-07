"""
core/services/groq_service.py
------------------------------
Structured prompt generation using Groq LLaMA 3.3-70b.
Each prompt framework has its own system instruction.
"""

import os
from groq import AsyncGroq
from fastapi import HTTPException
from typing import Literal

from commons.logger import logger as get_logger

log = get_logger("services.groq")

Framework = Literal["CO-STAR", "ROSES", "RFGF", "Tree of Thoughts", "Chain of Thought"]


# ---------------------------------------------------------------------------
# System prompts for each framework
# ---------------------------------------------------------------------------

_FRAMEWORK_SYSTEM_PROMPTS: dict[str, str] = {

    "CO-STAR": """You are an expert prompt engineer. The user will give you a rough idea or task in natural language.
Transform it into a structured prompt using the CO-STAR framework:

**Context**: Background information relevant to the task
**Objective**: The precise goal or outcome desired
**Style**: Tone, style, or persona for the response
**Tone**: Emotional tone (professional, casual, etc.)
**Audience**: Who the response is intended for
**Response**: The exact format of the output expected

Return only the formatted prompt. No explanations. Use markdown headers for each section.""",

    "ROSES": """You are an expert prompt engineer. The user will give you a rough idea or task in natural language.
Transform it into a structured prompt using the ROSES framework:

**Role**: The role the AI should assume
**Objective**: The specific task to accomplish
**Scenario**: The context or situation
**Expected Solution**: What a great response looks like
**Steps**: Step-by-step breakdown of how to approach the task

Return only the formatted prompt. No explanations. Use markdown headers for each section.""",

    "RFGF": """You are an expert prompt engineer. The user will give you a rough idea or task in natural language.
Transform it into a concise, clear prompt using the RFGF framework:

**Role**: Who the AI should be
**Format**: The output format (bullet list, paragraph, table, etc.)
**Goal**: The core objective in one sentence
**Fence**: Any constraints or things to avoid

Return only the formatted prompt. Keep it brief and clear. Use markdown headers.""",

    "Tree of Thoughts": """You are an expert prompt engineer. The user will give you a rough idea or task in natural language.
Transform it into a structured prompt using the Tree of Thoughts framework:

**Problem Statement**: Clearly define the problem
**Thought Branches**: 3 different approaches or angles to explore
**Evaluation Criteria**: How to judge which approach is best
**Selected Path**: Which branch to pursue and why
**Next Steps**: Concrete actions to take

Return only the formatted prompt. No explanations. Use markdown headers for each section.""",

    "Chain of Thought": """You are an expert prompt engineer. The user will give you a rough idea or task in natural language.
Transform it into a structured prompt using the Chain of Thought framework:

**Task**: The core programming or technical task
**Context**: Language, framework, constraints, or environment
**Step-by-Step Reasoning**: Break down the solution into logical steps
**Expected Output**: What the final code/solution should look like
**Edge Cases**: What corner cases or errors to handle

Return only the formatted prompt. No explanations. Use markdown headers for each section.""",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def generate_prompt(transcript: str, framework: str) -> str:
    """
    Generate a structured AI prompt from a transcript using Groq LLaMA 3.3.

    Args:
        transcript: The raw text from the STT step.
        framework:  One of CO-STAR | ROSES | RFGF | Tree of Thoughts | Chain of Thought.

    Returns:
        A formatted, structured prompt string.

    Raises:
        HTTPException 502: If Groq API call fails.
        HTTPException 400: If an unknown framework is requested.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        log.error("GROQ_API_KEY is not set in environment variables.")
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured.")

    system_prompt = _FRAMEWORK_SYSTEM_PROMPTS.get(framework)
    if not system_prompt:
        log.error("Unknown framework requested: '%s'", framework)
        raise HTTPException(
            status_code=400,
            detail=f"Unknown framework: '{framework}'. Choose from: {list(_FRAMEWORK_SYSTEM_PROMPTS.keys())}",
        )

    log.info("Generating prompt | framework=%s | transcript_chars=%d", framework, len(transcript))

    try:
        client = AsyncGroq(api_key=api_key)

        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript},
            ],
            temperature=0.3,
            max_tokens=900,
        )

        generated = response.choices[0].message.content.strip()

        if not generated:
            log.warning("Groq returned an empty response for framework=%s", framework)
            raise HTTPException(
                status_code=502,
                detail="Groq returned an empty response.",
            )

        log.info("Prompt generation successful | framework=%s | output_chars=%d", framework, len(generated))
        return generated

    except HTTPException:
        raise
    except Exception as e:
        log.exception("Groq prompt generation failed for framework=%s: %s", framework, e)
        raise HTTPException(
            status_code=502,
            detail=f"Groq prompt generation failed: {str(e)}",
        ) from e
