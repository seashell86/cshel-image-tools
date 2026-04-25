"""Regression test for FastMCP serialization of tool return values.

Earlier the tools returned a `list` containing a JSON string + the FastMCP
`Image` helper. FastMCP 1.27's structured-output path tried to pydantic-
validate that list and crashed with:
    Unable to serialize unknown type: <class 'mcp.server.fastmcp.utilities.types.Image'>

The fix is to return MCP protocol content blocks directly. This test
ensures every block in our tool response can be `model_dump`'d cleanly.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from mcp.types import ImageContent, TextContent

from cshel_image_tools.cost import compute_usage
from cshel_image_tools.tools._common import GenResult, to_tool_response


def _result(num_images: int = 1) -> GenResult:
    usage = compute_usage(
        SimpleNamespace(prompt_token_count=10, candidates_token_count=20, total_token_count=30),
        resolution="2K",
        images_returned=num_images,
        model="gemini-3-pro-image-preview",
    )
    return GenResult(
        paths=[Path(f"/tmp/fake-{i}.png") for i in range(num_images)],
        image_bytes=[b"\x89PNG\r\n\x1a\n" * 8] * num_images,
        mime_types=["image/png"] * num_images,
        text_parts=["model said hi"],
        usage=usage,
        safety={"blocked": False, "reasons": []},
    )


def test_response_contains_only_protocol_content_types() -> None:
    blocks = to_tool_response(_result(2))
    assert isinstance(blocks[0], TextContent)
    for b in blocks[1:]:
        assert isinstance(b, ImageContent)
    assert sum(1 for b in blocks if isinstance(b, ImageContent)) == 2


def test_every_block_is_pydantic_serializable() -> None:
    """Mirrors what FastMCP's structured_output codepath does."""
    blocks = to_tool_response(_result(1))
    for b in blocks:
        # model_dump_json must succeed; this is what crashed previously.
        encoded = b.model_dump_json()
        assert encoded
        # And round-trips through json.
        json.loads(encoded)


def test_text_block_carries_summary_payload() -> None:
    blocks = to_tool_response(_result(1), extra={"prompt": "x"})
    assert isinstance(blocks[0], TextContent)
    payload = json.loads(blocks[0].text)
    assert payload["prompt"] == "x"
    assert payload["paths"] == ["/tmp/fake-0.png"]
    assert payload["usage"]["images_returned"] == 1
    assert payload["safety"] == {"blocked": False, "reasons": []}


def test_image_block_data_is_base64() -> None:
    import base64

    blocks = to_tool_response(_result(1))
    img = blocks[1]
    assert isinstance(img, ImageContent)
    assert img.mimeType == "image/png"
    # Round-trip the data so we know it really is base64.
    assert base64.b64decode(img.data)
