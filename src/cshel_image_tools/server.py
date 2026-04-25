"""FastMCP server entry point. Registers all four image tools."""

from __future__ import annotations

import logging
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from cshel_image_tools import __version__
from cshel_image_tools.client import AuthError, build_client, describe_auth
from cshel_image_tools.config import load_config
from cshel_image_tools.tools.compose import compose_images as _compose
from cshel_image_tools.tools.edit import edit_image as _edit
from cshel_image_tools.tools.generate import generate_image as _generate
from cshel_image_tools.tools.upscale import upscale_image as _upscale

log = logging.getLogger("cshel_image_tools")


def _make_server() -> FastMCP:
    config = load_config()
    try:
        client = build_client(config)
    except AuthError as exc:
        sys.stderr.write(f"\n[cshel-image-tools] {exc}\n\n")
        raise SystemExit(2) from exc

    log.info(
        "cshel-image-tools v%s starting via %s; output_dir=%s; safety=%s",
        __version__,
        describe_auth(config),
        config.output_dir,
        config.safety_mode,
    )

    mcp = FastMCP(
        "cshel-image-tools",
        instructions=(
            "Google Nano Banana Pro (Gemini 3 Pro Image) tools: generate, edit, "
            "compose, and upscale images. Each tool returns the saved file paths, "
            "token usage, USD cost estimate, and the image content inline."
        ),
    )

    @mcp.tool()
    def generate_image(
        prompt: str,
        aspect_ratio: str = "1:1",
        resolution: str = "2K",
        num_images: int = 1,
        seed: int | None = None,
        negative_prompt: str | None = None,
    ) -> list[Any]:
        """Generate one or more images from a text prompt using Gemini 3 Pro Image (Nano Banana Pro).

        Args:
            prompt: What to generate. Be specific about subject, style, lighting, framing.
            aspect_ratio: One of 1:1, 16:9, 9:16, 4:3, 3:4, 2:3, 3:2, 5:4, 4:5, 21:9.
            resolution: One of 1K, 2K, 4K. 2K is a good balance; 4K costs more.
            num_images: 1-4 variations.
            seed: Optional integer for reproducibility.
            negative_prompt: Optional concepts to avoid (appended to prompt).
        """
        return _generate(
            client,
            config,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            num_images=num_images,
            seed=seed,
            negative_prompt=negative_prompt,
        )

    @mcp.tool()
    def edit_image(
        image: str,
        prompt: str,
        resolution: str = "2K",
    ) -> list[Any]:
        """Edit an existing image with a text instruction.

        Args:
            image: Absolute path to a local image OR a data URL (data:image/png;base64,...).
            prompt: Plain-language edit instruction (e.g., "add a small dog on the left").
            resolution: One of 1K, 2K, 4K.
        """
        return _edit(client, config, image=image, prompt=prompt, resolution=resolution)

    @mcp.tool()
    def compose_images(
        images: list[str],
        prompt: str,
        aspect_ratio: str = "1:1",
        resolution: str = "2K",
    ) -> list[Any]:
        """Combine 2-14 reference images into a single new image guided by a prompt.

        Useful for: putting a subject in a different scene, blending styles,
        merging characters, transferring outfits/lighting, multi-subject group shots.

        Args:
            images: List of 2-14 paths or data URLs.
            prompt: How the images should be combined.
            aspect_ratio: Output aspect ratio.
            resolution: One of 1K, 2K, 4K.
        """
        return _compose(
            client,
            config,
            images=images,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
        )

    @mcp.tool()
    def upscale_image(
        image: str,
        enhance_prompt: str | None = None,
    ) -> list[Any]:
        """Regenerate an image at 4K with content preserved, adding fine detail.

        Note: Nano Banana Pro has no dedicated upscale endpoint, so this is
        implemented as a 4K edit pass with a content-preserving prompt.

        Args:
            image: Absolute path or data URL.
            enhance_prompt: Optional override for the default detail-preserving prompt.
        """
        return _upscale(client, config, image=image, enhance_prompt=enhance_prompt)

    return mcp


def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    mcp = _make_server()
    mcp.run()
