"""Shared logic for all image tools: config build, API call, response packaging."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, get_args

from google import genai
from google.genai import types
from mcp.types import ImageContent, TextContent

from cshel_image_tools.config import AspectRatio, Config, Resolution
from cshel_image_tools.cost import Usage, compute_usage
from cshel_image_tools.images import save_image_bytes, to_mcp_image
from cshel_image_tools.safety import parse_safety, safety_settings_for

ToolResponse = list[TextContent | ImageContent]

log = logging.getLogger(__name__)

MODEL = "gemini-3-pro-image-preview"

VALID_ASPECT_RATIOS: tuple[str, ...] = get_args(AspectRatio)


@dataclass
class GenResult:
    paths: list[Path]
    image_bytes: list[bytes]
    mime_types: list[str]
    text_parts: list[str]
    usage: Usage
    safety: dict[str, Any]


def build_config(
    *,
    aspect_ratio: str | None,
    resolution: Resolution,
    seed: int | None,
    safety_mode: Any,
) -> types.GenerateContentConfig:
    image_kwargs: dict[str, Any] = {"image_size": resolution}
    if aspect_ratio:
        image_kwargs["aspect_ratio"] = aspect_ratio

    cfg_kwargs: dict[str, Any] = {
        "response_modalities": ["TEXT", "IMAGE"],
        "image_config": types.ImageConfig(**image_kwargs),
    }
    if seed is not None:
        cfg_kwargs["seed"] = seed

    settings = safety_settings_for(safety_mode)
    if settings:
        cfg_kwargs["safety_settings"] = settings

    return types.GenerateContentConfig(**cfg_kwargs)


def call_model(
    client: genai.Client,
    *,
    contents: list[Any],
    config: types.GenerateContentConfig,
) -> Any:
    """Call generate_content; retry without safety_settings if the model rejects them."""
    try:
        return client.models.generate_content(model=MODEL, contents=contents, config=config)
    except Exception as exc:  # noqa: BLE001
        if getattr(config, "safety_settings", None) and "safety_settings" in str(exc).lower():
            log.warning("Model rejected safety_settings; retrying without. (%s)", exc)
            stripped = types.GenerateContentConfig(
                response_modalities=config.response_modalities,
                image_config=config.image_config,
                seed=getattr(config, "seed", None),
            )
            return client.models.generate_content(model=MODEL, contents=contents, config=stripped)
        raise


def extract(response: Any) -> tuple[list[bytes], list[str], list[str]]:
    """Pull (image_bytes, mime_types, text_chunks) out of a response."""
    image_bytes: list[bytes] = []
    mime_types: list[str] = []
    texts: list[str] = []

    candidates = getattr(response, "candidates", None) or []
    for cand in candidates:
        content = getattr(cand, "content", None)
        if content is None:
            continue
        for part in getattr(content, "parts", None) or []:
            inline = getattr(part, "inline_data", None)
            if inline is not None and getattr(inline, "data", None):
                image_bytes.append(inline.data)
                mime_types.append(getattr(inline, "mime_type", "image/png") or "image/png")
                continue
            text = getattr(part, "text", None)
            if text:
                texts.append(text)

    return image_bytes, mime_types, texts


def package(
    response: Any,
    *,
    config: Config,
    resolution: Resolution,
    prefix: str,
) -> GenResult:
    image_bytes, mime_types, texts = extract(response)
    paths: list[Path] = []
    for idx, (data, mime) in enumerate(zip(image_bytes, mime_types, strict=True), start=1):
        paths.append(
            save_image_bytes(
                data,
                config.output_dir,
                prefix=prefix,
                index=idx,
                mime_type=mime,
            )
        )
    usage = compute_usage(
        getattr(response, "usage_metadata", None),
        resolution=resolution,
        images_returned=len(image_bytes),
        model=MODEL,
    )
    safety = parse_safety(response)
    return GenResult(
        paths=paths,
        image_bytes=image_bytes,
        mime_types=mime_types,
        text_parts=texts,
        usage=usage,
        safety=safety,
    )


def to_tool_response(result: GenResult, *, extra: dict[str, Any] | None = None) -> ToolResponse:
    summary: dict[str, Any] = {
        "paths": [str(p) for p in result.paths],
        "usage": result.usage.to_dict(),
        "safety": result.safety,
        "model_text": result.text_parts,
    }
    if extra:
        summary.update(extra)

    blocks: ToolResponse = [TextContent(type="text", text=json.dumps(summary, indent=2))]
    for data, mime in zip(result.image_bytes, result.mime_types, strict=True):
        blocks.append(to_mcp_image(data, mime))
    return blocks


def validate_aspect_ratio(value: str | None) -> str | None:
    if value is None:
        return None
    if value not in VALID_ASPECT_RATIOS:
        raise ValueError(
            f"aspect_ratio must be one of {VALID_ASPECT_RATIOS}, got {value!r}"
        )
    return value


def validate_resolution(value: str | None, fallback: Resolution) -> Resolution:
    if value is None:
        return fallback
    if value not in {"1K", "2K", "4K"}:
        raise ValueError(f"resolution must be one of '1K','2K','4K', got {value!r}")
    return value  # type: ignore[return-value]
