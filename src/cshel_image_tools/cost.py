"""Token-based cost estimation for Gemini 3 Pro Image output.

Prices below are based on Google's published rates for `gemini-3-pro-image-preview`
as of 2026-04. Update the constants when Google changes them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cshel_image_tools.config import Resolution

# verify-pricing: https://ai.google.dev/gemini-api/docs/pricing
# 1K and 2K outputs: 1120 tokens/image -> $0.134
# 4K outputs: 2000 tokens/image -> $0.24
PRICE_PER_IMAGE_USD: dict[Resolution, float] = {
    "1K": 0.134,
    "2K": 0.134,
    "4K": 0.24,
}

# Approximate input pricing for Gemini 3 Pro (text + image input). Conservative
# upper bound; refine when per-token figures are needed for billing.
INPUT_PRICE_PER_MILLION_TOKENS_USD = 2.00


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int
    output_tokens: int
    total_tokens: int
    images_returned: int
    cost_usd: float
    model: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "images_returned": self.images_returned,
            "cost_usd": round(self.cost_usd, 6),
            "model": self.model,
        }


def _attr(obj: Any, name: str, default: int = 0) -> int:
    return int(getattr(obj, name, None) or default)


def compute_usage(
    response_usage: Any,
    *,
    resolution: Resolution,
    images_returned: int,
    model: str,
) -> Usage:
    prompt_tokens = _attr(response_usage, "prompt_token_count")
    output_tokens = _attr(response_usage, "candidates_token_count")
    total_tokens = _attr(response_usage, "total_token_count") or (prompt_tokens + output_tokens)

    image_cost = PRICE_PER_IMAGE_USD.get(resolution, 0.0) * images_returned
    input_cost = (prompt_tokens / 1_000_000) * INPUT_PRICE_PER_MILLION_TOKENS_USD
    cost_usd = image_cost + input_cost

    return Usage(
        prompt_tokens=prompt_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        images_returned=images_returned,
        cost_usd=cost_usd,
        model=model,
    )
