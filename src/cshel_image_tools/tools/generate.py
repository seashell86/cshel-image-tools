"""generate_image: text prompt -> image(s)."""

from __future__ import annotations

from typing import Any

from google import genai

from cshel_image_tools.config import Config
from cshel_image_tools.tools._common import (
    build_config,
    call_model,
    package,
    to_tool_response,
    validate_aspect_ratio,
    validate_resolution,
)

MAX_IMAGES = 4


def generate_image(
    client: genai.Client,
    config: Config,
    *,
    prompt: str,
    aspect_ratio: str | None = None,
    resolution: str | None = None,
    num_images: int = 1,
    seed: int | None = None,
    negative_prompt: str | None = None,
) -> list[Any]:
    if not prompt or not prompt.strip():
        raise ValueError("prompt is required")
    if not 1 <= num_images <= MAX_IMAGES:
        raise ValueError(f"num_images must be between 1 and {MAX_IMAGES}")

    aspect = validate_aspect_ratio(aspect_ratio) or "1:1"
    res = validate_resolution(resolution, config.default_resolution)

    full_prompt = prompt.strip()
    if negative_prompt:
        full_prompt = f"{full_prompt}\n\nAvoid the following: {negative_prompt.strip()}"
    if num_images > 1:
        full_prompt = f"{full_prompt}\n\nProduce {num_images} distinct variations."

    gen_config = build_config(
        aspect_ratio=aspect,
        resolution=res,
        seed=seed,
        safety_mode=config.safety_mode,
    )

    response = call_model(client, contents=[full_prompt], config=gen_config)
    result = package(response, config=config, resolution=res, prefix="generate")
    return to_tool_response(
        result,
        extra={
            "prompt": prompt,
            "aspect_ratio": aspect,
            "resolution": res,
            "seed": seed,
            "negative_prompt": negative_prompt,
        },
    )
