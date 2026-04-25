"""Image I/O helpers: load inputs, save outputs, build MCP image content blocks."""

from __future__ import annotations

import base64
import io
import re
from datetime import UTC, datetime
from pathlib import Path

from mcp.server.fastmcp import Image as MCPImage
from PIL import Image as PILImage

DATA_URL_RE = re.compile(r"^data:(?P<mime>image/[a-zA-Z0-9.+-]+);base64,(?P<data>.+)$", re.DOTALL)


def load_input_image(value: str) -> PILImage.Image:
    """Load an image from either a filesystem path or a data URL."""
    match = DATA_URL_RE.match(value.strip())
    if match:
        raw = base64.b64decode(match.group("data"))
        return PILImage.open(io.BytesIO(raw))

    path = Path(value).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Input image not found: {value!r}")
    return PILImage.open(path)


def save_image_bytes(
    image_bytes: bytes,
    output_dir: Path,
    *,
    prefix: str,
    index: int,
    mime_type: str = "image/png",
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ext = mime_type.split("/")[-1].replace("jpeg", "jpg")
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    name = f"{prefix}-{timestamp}-{index:02d}.{ext}"
    path = output_dir / name
    path.write_bytes(image_bytes)
    return path


def to_mcp_image(image_bytes: bytes, mime_type: str = "image/png") -> MCPImage:
    fmt = mime_type.split("/")[-1]
    return MCPImage(data=image_bytes, format=fmt)
