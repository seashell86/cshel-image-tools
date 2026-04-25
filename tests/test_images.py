from __future__ import annotations

import base64
import io
from pathlib import Path

import pytest
from PIL import Image as PILImage

from cshel_image_tools.images import load_input_image, save_image_bytes


def _png_bytes(color: str = "red") -> bytes:
    img = PILImage.new("RGB", (8, 8), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_save_image_bytes_writes_file(tmp_path: Path) -> None:
    path = save_image_bytes(_png_bytes(), tmp_path, prefix="test", index=1)
    assert path.exists()
    assert path.suffix == ".png"
    assert path.stat().st_size > 0


def test_save_jpeg_extension(tmp_path: Path) -> None:
    path = save_image_bytes(b"fake", tmp_path, prefix="t", index=1, mime_type="image/jpeg")
    assert path.suffix == ".jpg"


def test_load_from_path(tmp_path: Path) -> None:
    p = tmp_path / "x.png"
    p.write_bytes(_png_bytes("blue"))
    img = load_input_image(str(p))
    assert img.size == (8, 8)


def test_load_from_data_url() -> None:
    data_url = "data:image/png;base64," + base64.b64encode(_png_bytes("green")).decode()
    img = load_input_image(data_url)
    assert img.size == (8, 8)


def test_load_missing_path_errors(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_input_image(str(tmp_path / "nope.png"))
