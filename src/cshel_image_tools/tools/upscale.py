"""upscale_image: regenerate input image at 4K with detail-preserving prompt.

Note: Nano Banana Pro has no dedicated upscale endpoint. This tool implements
upscaling as an edit pass pinned to image_size=4K.
"""

from __future__ import annotations

from typing import Any

from google import genai

from cshel_image_tools.config import Config
from cshel_image_tools.images import load_input_image
from cshel_image_tools.tools._common import build_config, call_model, package, to_tool_response

DEFAULT_PROMPT = (
    "Increase resolution and add fine, photoreal detail. "
    "Preserve all subjects, composition, colors, and style exactly."
)


def upscale_image(
    client: genai.Client,
    config: Config,
    *,
    image: str,
    enhance_prompt: str | None = None,
) -> list[Any]:
    if not image or not image.strip():
        raise ValueError("image (path or data URL) is required")

    pil = load_input_image(image)
    prompt = (enhance_prompt or DEFAULT_PROMPT).strip()

    gen_config = build_config(
        aspect_ratio=None,
        resolution="4K",
        seed=None,
        safety_mode=config.safety_mode,
    )

    response = call_model(client, contents=[prompt, pil], config=gen_config)
    result = package(response, config=config, resolution="4K", prefix="upscale")
    return to_tool_response(
        result,
        extra={
            "prompt": prompt,
            "input_image": image,
            "resolution": "4K",
            "note": "Implemented as a 4K edit pass; not a dedicated upscale endpoint.",
        },
    )
