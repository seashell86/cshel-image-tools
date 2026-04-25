"""Server configuration loaded from environment variables."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

APP_DIR_NAME = "cshel-image-tools"

Resolution = Literal["1K", "2K", "4K"]
SafetyMode = Literal["standard", "strict"]
AspectRatio = Literal[
    "1:1", "16:9", "9:16", "4:3", "3:4", "2:3", "3:2",
    "5:4", "4:5", "21:9", "1:4", "4:1", "1:8", "8:1",
]

VALID_RESOLUTIONS: tuple[Resolution, ...] = ("1K", "2K", "4K")
VALID_SAFETY_MODES: tuple[SafetyMode, ...] = ("standard", "strict")

DEFAULT_OUTPUT_DIR = "generated-images"
DEFAULT_RESOLUTION: Resolution = "2K"
DEFAULT_SAFETY: SafetyMode = "standard"


@dataclass(frozen=True)
class Config:
    output_dir: Path
    default_resolution: Resolution
    safety_mode: SafetyMode
    use_vertex: bool
    api_key: str | None
    project: str | None
    location: str | None

    @property
    def auth_mode(self) -> Literal["vertex", "ai_studio"]:
        return "vertex" if self.use_vertex else "ai_studio"


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def user_config_paths() -> list[Path]:
    """Per-user .env candidate paths in priority order. First existing file wins.

    Process env always wins over file values; a project-local `./.env` (loaded
    separately) wins over these user-scoped fallbacks.
    """
    home = Path.home()
    xdg_root = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")

    paths: list[Path] = [xdg_root / APP_DIR_NAME / ".env"]
    if sys.platform == "darwin":
        paths.append(home / "Library" / "Application Support" / APP_DIR_NAME / ".env")
    elif sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            paths.append(Path(appdata) / APP_DIR_NAME / ".env")

    seen: set[Path] = set()
    unique: list[Path] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def _load_dotenv_chain() -> None:
    """Load .env files in priority order: cwd, then per-user fallbacks.

    `python-dotenv` does not override existing env vars by default, so the
    first source to define a variable wins. Order:
      1. process environment (already populated; preserved)
      2. ./.env (project-local)
      3. user config dir(s) (~/.config/cshel-image-tools/.env, etc.)
    """
    project_env = Path.cwd() / ".env"
    if project_env.is_file():
        load_dotenv(project_env)
    for candidate in user_config_paths():
        if candidate.is_file():
            load_dotenv(candidate)
            break


def load_config() -> Config:
    _load_dotenv_chain()

    output_dir = Path(os.getenv("CSHEL_IMAGE_OUTPUT_DIR") or DEFAULT_OUTPUT_DIR).expanduser().resolve()

    resolution = os.getenv("CSHEL_IMAGE_DEFAULT_RESOLUTION", DEFAULT_RESOLUTION)
    if resolution not in VALID_RESOLUTIONS:
        raise ValueError(
            f"CSHEL_IMAGE_DEFAULT_RESOLUTION must be one of {VALID_RESOLUTIONS}, got {resolution!r}"
        )

    safety = os.getenv("CSHEL_IMAGE_SAFETY", DEFAULT_SAFETY)
    if safety not in VALID_SAFETY_MODES:
        raise ValueError(
            f"CSHEL_IMAGE_SAFETY must be one of {VALID_SAFETY_MODES}, got {safety!r}"
        )

    use_vertex = _truthy(os.getenv("GOOGLE_GENAI_USE_VERTEXAI"))

    return Config(
        output_dir=output_dir,
        default_resolution=resolution,
        safety_mode=safety,
        use_vertex=use_vertex,
        api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION"),
    )
