"""Safety mode plumbing.

Image-model support for `safety_settings` on `GenerateContentConfig` is not
explicitly documented for `gemini-3-pro-image-preview` as of 2026-04. We pass
the strict bundle when requested; the calling tool catches any 'unsupported
field' error and retries without it. See README for details.
"""

from __future__ import annotations

import logging
from typing import Any

from google.genai import types

from cshel_image_tools.config import SafetyMode

log = logging.getLogger(__name__)

_STRICT_CATEGORIES = (
    "HARM_CATEGORY_HATE_SPEECH",
    "HARM_CATEGORY_HARASSMENT",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "HARM_CATEGORY_DANGEROUS_CONTENT",
)


def safety_settings_for(mode: SafetyMode) -> list[types.SafetySetting] | None:
    if mode == "standard":
        return None
    return [
        types.SafetySetting(
            category=cat,  # type: ignore[arg-type]
            threshold="BLOCK_LOW_AND_ABOVE",  # type: ignore[arg-type]
        )
        for cat in _STRICT_CATEGORIES
    ]


def parse_safety(response: Any) -> dict[str, Any]:
    """Pull blocked status + reasons from a generate_content response."""
    blocked = False
    reasons: list[str] = []

    feedback = getattr(response, "prompt_feedback", None)
    if feedback is not None:
        block_reason = getattr(feedback, "block_reason", None)
        if block_reason:
            blocked = True
            reasons.append(f"prompt:{block_reason}")
        for rating in getattr(feedback, "safety_ratings", []) or []:
            if getattr(rating, "blocked", False):
                blocked = True
                reasons.append(f"prompt:{rating.category}")

    for cand in getattr(response, "candidates", []) or []:
        finish = getattr(cand, "finish_reason", None)
        if finish and str(finish).upper().endswith("SAFETY"):
            blocked = True
            reasons.append(f"candidate:{finish}")
        for rating in getattr(cand, "safety_ratings", []) or []:
            if getattr(rating, "blocked", False):
                blocked = True
                reasons.append(f"candidate:{rating.category}")

    return {"blocked": blocked, "reasons": reasons}
