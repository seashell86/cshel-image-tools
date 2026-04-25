"""Factory for the google-genai client. Auto-detects AI Studio vs Vertex AI."""

from __future__ import annotations

from google import genai

from cshel_image_tools.config import Config


class AuthError(RuntimeError):
    """Raised when no valid auth path is configured."""


def build_client(config: Config) -> genai.Client:
    if config.use_vertex:
        if not config.project or not config.location:
            raise AuthError(
                "Vertex AI mode requires GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION."
            )
        return genai.Client(
            vertexai=True,
            project=config.project,
            location=config.location,
        )

    if not config.api_key:
        raise AuthError(
            "No auth configured. Set GEMINI_API_KEY for the Gemini API, "
            "or set GOOGLE_GENAI_USE_VERTEXAI=true with GOOGLE_CLOUD_PROJECT and "
            "GOOGLE_CLOUD_LOCATION for Vertex AI."
        )
    return genai.Client(api_key=config.api_key)


def describe_auth(config: Config) -> str:
    if config.use_vertex:
        return f"Vertex AI (project={config.project}, location={config.location})"
    return "Gemini API (AI Studio key)"
