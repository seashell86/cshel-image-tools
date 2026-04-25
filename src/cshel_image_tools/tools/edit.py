"""edit_image: input image + prompt -> edited image."""

from __future__ import annotations

from google import genai

from cshel_image_tools.config import Config
from cshel_image_tools.images import load_input_image
from cshel_image_tools.tools._common import (
    ToolResponse,
    build_config,
    call_model,
    package,
    to_tool_response,
    validate_resolution,
)


def edit_image(
    client: genai.Client,
    config: Config,
    *,
    image: str,
    prompt: str,
    resolution: str | None = None,
) -> ToolResponse:
    if not prompt or not prompt.strip():
        raise ValueError("prompt is required")
    if not image or not image.strip():
        raise ValueError("image (path or data URL) is required")

    pil = load_input_image(image)
    res = validate_resolution(resolution, config.default_resolution)

    gen_config = build_config(
        aspect_ratio=None,  # let model preserve input aspect when None
        resolution=res,
        seed=None,
        safety_mode=config.safety_mode,
    )

    response = call_model(client, contents=[prompt.strip(), pil], config=gen_config)
    result = package(response, config=config, resolution=res, prefix="edit")
    return to_tool_response(
        result,
        extra={
            "prompt": prompt,
            "input_image": image,
            "resolution": res,
        },
    )
