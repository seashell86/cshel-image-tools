# cshel-image-tools

[![PyPI](https://img.shields.io/pypi/v/cshel-image-tools.svg)](https://pypi.org/project/cshel-image-tools/)
[![Python](https://img.shields.io/pypi/pyversions/cshel-image-tools.svg)](https://pypi.org/project/cshel-image-tools/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An MCP server that gives any MCP-aware client (Claude Desktop, Claude Code, Cursor, Continue, etc.) access to Google's **Nano Banana Pro** — a.k.a. **Gemini 3 Pro Image** (`gemini-3-pro-image-preview`) — for generation, editing, multi-image composition, and 4K upscaling.

- **Generate** images from a prompt (1K/2K/4K, full aspect-ratio set)
- **Edit** an existing image with a text instruction
- **Compose** 2–14 reference images into a single new one
- **Upscale** any image to 4K with content preserved
- Returns saved file paths **and** the image inline so the calling LLM can see it
- Reports per-call **token usage and USD cost**
- Optional **strict safety mode** for hosted/shared deployments
- Works with both the **Gemini API (AI Studio key)** and **Vertex AI** — auto-detected

## Install & run

This server is published to PyPI. The fastest way to use it is with `uv`:

```bash
# One-shot run (no global install)
uvx cshel-image-tools
```

Or install for development:

```bash
git clone https://github.com/seashell86/cshel-image-tools
cd cshel-image-tools
uv sync --extra dev
uv run cshel-image-tools
```

## Authentication

Set **one** of the following.

### Gemini API (simplest)

```bash
export GEMINI_API_KEY="your-key-from-aistudio.google.com"
```

### Vertex AI (org/prod)

```bash
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT="your-gcp-project"
export GOOGLE_CLOUD_LOCATION="us-central1"
gcloud auth application-default login   # one-time
```

The server picks the path on startup based on env vars.

### Where the server looks for your key

Resolved in priority order (first source wins):

1. **Process environment** — anything passed in the MCP client's `env` block, exported in your shell, or already set when the server is launched.
2. **Project-local `.env`** — `./.env` in whatever directory the server is launched from. Useful for `uv run` from a checkout.
3. **Per-user config** — `~/.config/cshel-image-tools/.env`, plus `~/Library/Application Support/cshel-image-tools/.env` on macOS. Loaded regardless of cwd, so this is the cleanest place to put a key once and have every MCP client pick it up.

The server ships a helper for the third option:

```bash
uvx cshel-image-tools init     # writes ~/.config/cshel-image-tools/.env (chmod 600)
uvx cshel-image-tools where    # prints the lookup paths and which exist
```

After `init`, edit the file to paste your key. No more pasting into Claude Desktop / Claude Code config JSON.

## MCP client config

### Claude Desktop / Claude Code (`mcpServers` block)

If you ran `cshel-image-tools init`, the `env` block is optional — the server will pick up your key from `~/.config/cshel-image-tools/.env`:

```json
{
  "mcpServers": {
    "cshel-image-tools": {
      "command": "uvx",
      "args": ["cshel-image-tools"]
    }
  }
}
```

Or pass everything inline if you prefer:

```json
{
  "mcpServers": {
    "cshel-image-tools": {
      "command": "uvx",
      "args": ["cshel-image-tools"],
      "env": {
        "GEMINI_API_KEY": "your-key",
        "CSHEL_IMAGE_OUTPUT_DIR": "/Users/you/Pictures/nano-banana"
      }
    }
  }
}
```

See [`examples/`](examples/) for ready-to-paste configs.

### Claude Code (CLI)

```bash
claude mcp add cshel-image-tools -- uvx cshel-image-tools
```

## Tools

All tools save images to `CSHEL_IMAGE_OUTPUT_DIR` (default `./generated-images`) **and** return them inline so the model can react to what was generated. Every result also includes:

- `paths`: absolute paths to saved files
- `usage`: prompt/output/total tokens, model, image count
- `cost_usd`: USD estimate
- `safety`: `{ blocked: bool, reasons: [...] }`

### `generate_image`
Text → image.

| arg | type | default | notes |
|---|---|---|---|
| `prompt` | str | — | required |
| `aspect_ratio` | str | `"1:1"` | `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `5:4`, `4:5`, `21:9`, `2:3`, `3:2` |
| `resolution` | str | `"2K"` | `1K`, `2K`, `4K` |
| `num_images` | int | `1` | 1–4 |
| `seed` | int? | `None` | reproducibility |
| `negative_prompt` | str? | `None` | concepts to avoid |

### `edit_image`
Image + prompt → edited image.

| arg | type | default |
|---|---|---|
| `image` | str (path or `data:image/...;base64,...`) | — |
| `prompt` | str | — |
| `resolution` | str | `"2K"` |

### `compose_images`
2–14 references + prompt → one composed image. Great for: subject-in-scene, character consistency, outfit transfer, group shots.

| arg | type | default |
|---|---|---|
| `images` | list[str] (paths or data URLs) | — |
| `prompt` | str | — |
| `aspect_ratio` | str | `"1:1"` |
| `resolution` | str | `"2K"` |

### `upscale_image`
Regenerate at 4K with content preserved. Implemented as a 4K edit pass — Nano Banana Pro doesn't have a dedicated upscale endpoint.

| arg | type | default |
|---|---|---|
| `image` | str (path or data URL) | — |
| `enhance_prompt` | str? | content-preserving default |

## Configuration

| env var | purpose | default |
|---|---|---|
| `GEMINI_API_KEY` | AI Studio key (auth path A) | — |
| `GOOGLE_API_KEY` | alias for `GEMINI_API_KEY` | — |
| `GOOGLE_GENAI_USE_VERTEXAI` | switch to Vertex AI (auth path B) | `false` |
| `GOOGLE_CLOUD_PROJECT` | Vertex project ID | — |
| `GOOGLE_CLOUD_LOCATION` | Vertex region (e.g. `us-central1`) | — |
| `CSHEL_IMAGE_OUTPUT_DIR` | where images are written | `./generated-images` |
| `CSHEL_IMAGE_DEFAULT_RESOLUTION` | default if a tool doesn't specify | `2K` |
| `CSHEL_IMAGE_SAFETY` | `standard` or `strict` | `standard` |

A `.env` file in the working directory is auto-loaded.

## Cost

Estimates are computed from `response.usage_metadata` and the published Gemini 3 Pro Image rates:

| resolution | tokens / image | est. USD / image |
|---|---|---|
| 1K | 1120 | $0.134 |
| 2K | 1120 | $0.134 |
| 4K | 2000 | $0.240 |

Plus a small input-token cost. See `src/cshel_image_tools/cost.py` to update rates.

## Safety

`CSHEL_IMAGE_SAFETY=strict` sends `BLOCK_LOW_AND_ABOVE` thresholds for the four standard harm categories. If the model rejects `safety_settings` (image-model support is preview-stage and not 100% documented), the server logs a warning and retries without — so strict mode is best-effort. Each tool result also includes a parsed `safety: { blocked, reasons }` block from `prompt_feedback` and candidate finish reasons.

## Development

```bash
uv sync --extra dev
uv run ruff check .
uv run mypy src
uv run pytest                                 # unit tests
GEMINI_API_KEY=... uv run pytest -k smoke     # hits the live API
```

## Troubleshooting

- **`AuthError` on startup** → set `GEMINI_API_KEY` or the Vertex trio.
- **`uvx` can't find package after publish** → wait ~30s for PyPI CDN, then retry.
- **Images look low-detail at 1K** → bump `resolution` to `2K` or `4K`.
- **`safety_settings` warning in logs** → expected when the image model rejects the field; standard safety still applies server-side.
- **Slow first run via `uvx`** → `uvx` resolves and caches deps the first time; subsequent runs are fast.

## License

MIT — see [LICENSE](LICENSE).
