from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from cshel_image_tools.config import DEFAULT_RESOLUTION, DEFAULT_SAFETY, load_config

ENV_KEYS = (
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_GENAI_USE_VERTEXAI",
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_CLOUD_LOCATION",
    "CSHEL_IMAGE_OUTPUT_DIR",
    "CSHEL_IMAGE_DEFAULT_RESOLUTION",
    "CSHEL_IMAGE_SAFETY",
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    # Prevent a real .env from leaking in.
    monkeypatch.chdir(os.path.dirname(__file__))
    yield


def test_defaults_when_only_api_key_set(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("CSHEL_IMAGE_OUTPUT_DIR", str(tmp_path / "out"))
    cfg = load_config()
    assert cfg.api_key == "k"
    assert cfg.use_vertex is False
    assert cfg.auth_mode == "ai_studio"
    assert cfg.output_dir == (tmp_path / "out").resolve()
    assert cfg.default_resolution == DEFAULT_RESOLUTION
    assert cfg.safety_mode == DEFAULT_SAFETY


def test_vertex_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "p")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    cfg = load_config()
    assert cfg.use_vertex is True
    assert cfg.auth_mode == "vertex"
    assert cfg.project == "p"
    assert cfg.location == "us-central1"


def test_invalid_resolution_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("CSHEL_IMAGE_DEFAULT_RESOLUTION", "8K")
    with pytest.raises(ValueError, match="CSHEL_IMAGE_DEFAULT_RESOLUTION"):
        load_config()


def test_invalid_safety_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("CSHEL_IMAGE_SAFETY", "paranoid")
    with pytest.raises(ValueError, match="CSHEL_IMAGE_SAFETY"):
        load_config()


@pytest.mark.parametrize("value", ["true", "TRUE", "1", "yes", "on"])
def test_vertex_truthy_values(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", value)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "p")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    assert load_config().use_vertex is True


@pytest.mark.parametrize("value", ["false", "0", "no", "", "off"])
def test_vertex_falsy_values(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", value)
    assert load_config().use_vertex is False
