from __future__ import annotations

from types import SimpleNamespace

import pytest

from cshel_image_tools.cost import PRICE_PER_IMAGE_USD, compute_usage


def _meta(prompt: int, output: int) -> SimpleNamespace:
    return SimpleNamespace(
        prompt_token_count=prompt,
        candidates_token_count=output,
        total_token_count=prompt + output,
    )


@pytest.mark.parametrize(
    "resolution,n,expected",
    [
        ("1K", 1, PRICE_PER_IMAGE_USD["1K"]),
        ("2K", 1, PRICE_PER_IMAGE_USD["2K"]),
        ("4K", 1, PRICE_PER_IMAGE_USD["4K"]),
        ("2K", 3, PRICE_PER_IMAGE_USD["2K"] * 3),
        ("4K", 2, PRICE_PER_IMAGE_USD["4K"] * 2),
    ],
)
def test_image_cost_matches_resolution(resolution: str, n: int, expected: float) -> None:
    usage = compute_usage(_meta(0, 0), resolution=resolution, images_returned=n, model="m")  # type: ignore[arg-type]
    assert usage.cost_usd == pytest.approx(expected, abs=1e-6)


def test_input_tokens_add_to_cost() -> None:
    base = compute_usage(_meta(0, 0), resolution="2K", images_returned=1, model="m")
    with_input = compute_usage(_meta(1_000_000, 0), resolution="2K", images_returned=1, model="m")
    assert with_input.cost_usd > base.cost_usd


def test_handles_missing_metadata() -> None:
    usage = compute_usage(None, resolution="2K", images_returned=1, model="m")
    assert usage.prompt_tokens == 0
    assert usage.output_tokens == 0
    assert usage.cost_usd >= PRICE_PER_IMAGE_USD["2K"] - 1e-6


def test_to_dict_keys() -> None:
    usage = compute_usage(_meta(10, 20), resolution="2K", images_returned=1, model="m")
    d = usage.to_dict()
    assert set(d) == {"prompt_tokens", "output_tokens", "total_tokens", "images_returned", "cost_usd", "model"}
