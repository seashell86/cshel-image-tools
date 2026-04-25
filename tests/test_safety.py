from __future__ import annotations

from types import SimpleNamespace

from cshel_image_tools.safety import parse_safety, safety_settings_for


def test_standard_returns_none() -> None:
    assert safety_settings_for("standard") is None


def test_strict_returns_four_categories() -> None:
    settings = safety_settings_for("strict")
    assert settings is not None
    assert len(settings) == 4


def test_parse_clean_response() -> None:
    response = SimpleNamespace(
        prompt_feedback=None,
        candidates=[SimpleNamespace(finish_reason="STOP", safety_ratings=[])],
    )
    assert parse_safety(response) == {"blocked": False, "reasons": []}


def test_parse_blocked_prompt() -> None:
    response = SimpleNamespace(
        prompt_feedback=SimpleNamespace(block_reason="SAFETY", safety_ratings=[]),
        candidates=[],
    )
    result = parse_safety(response)
    assert result["blocked"] is True
    assert any("SAFETY" in r for r in result["reasons"])


def test_parse_blocked_candidate() -> None:
    response = SimpleNamespace(
        prompt_feedback=None,
        candidates=[SimpleNamespace(finish_reason="SAFETY", safety_ratings=[])],
    )
    result = parse_safety(response)
    assert result["blocked"] is True
