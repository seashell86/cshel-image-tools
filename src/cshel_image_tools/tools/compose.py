"""compose_images: 2-14 reference images + prompt -> single composed image."""

from __future__ import annotations

from typing import Any

from google import genai

from cshel_image_tools.config import Config
from cshel_image_tools.images import load_input_image
from cshel_image_tools.tools._common import (
    ToolResponse,
    build_config,
    call_model,
    package,
    to_tool_response,
    validate_aspect_ratio,
    validate_resolution,
)

MIN_IMAGES = 2
MAX_IMAGES = 14


def compose_images(
    client: genai.Client,
    config: Config,
    *,
    images: list[str],
    prompt: str,
    aspect_ratio: str | None = None,
    resolution: str | None = None,
) -> ToolResponse:
    if not prompt or not prompt.strip():
        raise ValueError("prompt is required")
    if not images or not isinstance(images, list):
        raise ValueError("images must be a list of paths or data URLs")
    if not MIN_IMAGES <= len(images) <= MAX_IMAGES:
        raise ValueError(
            f"compose_images requires {MIN_IMAGES}-{MAX_IMAGES} reference images "
            f"(got {len(images)})"
        )

    aspect = validate_aspect_ratio(aspect_ratio) or "1:1"
    res = validate_resolution(resolution, config.default_resolution)

    pil_images = [load_input_image(p) for p in images]
    contents: list[Any] = [prompt.strip(), *pil_images]

    gen_config = build_config(
        aspect_ratio=aspect,
        resolution=res,
        seed=None,
        safety_mode=config.safety_mode,
    )

    response = call_model(client, contents=contents, config=gen_config)
    result = package(response, config=config, resolution=res, prefix="compose")
    return to_tool_response(
        result,
        extra={
            "prompt": prompt,
            "input_images": images,
            "aspect_ratio": aspect,
            "resolution": res,
        },
    )
