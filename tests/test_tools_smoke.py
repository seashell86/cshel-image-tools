"""Live API smoke tests. Skipped unless GEMINI_API_KEY is set.

Run with:
    GEMINI_API_KEY=... uv run pytest -k smoke -s
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"),
    reason="No GEMINI_API_KEY/GOOGLE_API_KEY set; skipping live API smoke tests.",
)


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("CSHEL_IMAGE_OUTPUT_DIR", str(tmp_path))
    return tmp_path


def _config_and_client():  # noqa: ANN202 - test helper
    from cshel_image_tools.client import build_client
    from cshel_image_tools.config import load_config

    cfg = load_config()
    return cfg, build_client(cfg)


def _payload(blocks: list) -> dict:
    return json.loads(blocks[0])


def test_generate_smoke(env: Path) -> None:
    from cshel_image_tools.tools.generate import generate_image

    cfg, client = _config_and_client()
    blocks = generate_image(
        client,
        cfg,
        prompt="A red apple on a wooden table, soft daylight, photoreal.",
        resolution="1K",
    )
    payload = _payload(blocks)
    assert payload["paths"], "expected at least one saved path"
    assert Path(payload["paths"][0]).exists()
    assert payload["usage"]["images_returned"] >= 1
    assert payload["usage"]["cost_usd"] > 0


def test_edit_smoke(env: Path) -> None:
    from cshel_image_tools.tools.edit import edit_image
    from cshel_image_tools.tools.generate import generate_image

    cfg, client = _config_and_client()
    first = generate_image(client, cfg, prompt="A green pear on white background.", resolution="1K")
    src = json.loads(first[0])["paths"][0]

    blocks = edit_image(client, cfg, image=src, prompt="Make the pear yellow.", resolution="1K")
    payload = _payload(blocks)
    assert payload["paths"]
    assert Path(payload["paths"][0]).exists()
