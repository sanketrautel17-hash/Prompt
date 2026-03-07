"""
core/services/intent_service.py
---------------------------------
Keyword-based intent detection from a transcript.
Maps detected intent → prompt framework.

Intent → Framework mapping:
  writing / creative  →  CO-STAR
  coding / technical  →  Chain of Thought
  business / strategy →  ROSES
  problem_solving     →  Tree of Thoughts
  quick / simple      →  RFGF (default)
"""

from typing import Literal

Intent = Literal["writing", "coding", "business", "problem_solving", "quick"]
Framework = Literal["CO-STAR", "ROSES", "RFGF", "Tree of Thoughts", "Chain of Thought"]


# ---------------------------------------------------------------------------
# Keyword → Intent mapping
# ---------------------------------------------------------------------------

_INTENT_KEYWORDS: dict[Intent, list[str]] = {
    "writing": [
        "write", "writing", "essay", "blog", "article", "story", "creative",
        "email", "letter", "draft", "content", "copy", "poem", "script",
        "describe", "explain", "summarize", "document",
    ],
    "coding": [
        "code", "coding", "program", "function", "bug", "debug", "implement",
        "algorithm", "api", "database", "sql", "python", "javascript",
        "class", "method", "refactor", "test", "unit test", "fix",
        "script", "developer", "software", "error", "exception",
    ],
    "business": [
        "business", "strategy", "plan", "market", "startup", "product",
        "revenue", "growth", "customer", "sales", "pitch", "investor",
        "roi", "kpi", "team", "management", "launch", "pricing", "brand",
        "competitive", "analysis", "proposal",
    ],
    "problem_solving": [
        "problem", "solve", "solution", "decision", "choose", "compare",
        "evaluate", "options", "tradeoff", "pros and cons", "analyze",
        "issue", "challenge", "improve", "optimize", "troubleshoot",
        "diagnose", "root cause", "brainstorm",
    ],
    "quick": [
        "quick", "short", "brief", "simple", "fast", "tldr", "summary",
        "one line", "just", "what is", "how to", "define",
    ],
}

# Framework assigned to each intent
_INTENT_TO_FRAMEWORK: dict[Intent, Framework] = {
    "writing":         "CO-STAR",
    "coding":          "Chain of Thought",
    "business":        "ROSES",
    "problem_solving": "Tree of Thoughts",
    "quick":           "RFGF",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_intent(transcript: str) -> tuple[Intent, Framework]:
    """
    Detect the intent from a transcript using keyword matching.
    Returns (intent, framework) tuple.

    Scoring: each keyword match adds 1 point to that intent's score.
    Highest score wins. Defaults to ("quick", "RFGF") if no match.

    Args:
        transcript: Raw text from the STT step.

    Returns:
        Tuple of (detected_intent, prompt_framework).
    """
    lower = transcript.lower()
    scores: dict[Intent, int] = {intent: 0 for intent in _INTENT_KEYWORDS}

    for intent, keywords in _INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lower:
                scores[intent] += 1

    # Pick highest scoring intent; default to "quick" on tie/zero
    best_intent: Intent = max(scores, key=lambda k: scores[k])

    if scores[best_intent] == 0:
        best_intent = "quick"

    framework = _INTENT_TO_FRAMEWORK[best_intent]
    return best_intent, framework
