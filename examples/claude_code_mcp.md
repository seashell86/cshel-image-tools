# Using cshel-image-tools with Claude Code

## Add it (CLI)

Quickest, with a Gemini API key:

```bash
claude mcp add cshel-image-tools \
  --env GEMINI_API_KEY=your-key \
  --env CSHEL_IMAGE_OUTPUT_DIR="$HOME/Pictures/nano-banana" \
  -- uvx cshel-image-tools
```

With Vertex AI:

```bash
claude mcp add cshel-image-tools \
  --env GOOGLE_GENAI_USE_VERTEXAI=true \
  --env GOOGLE_CLOUD_PROJECT=your-project \
  --env GOOGLE_CLOUD_LOCATION=us-central1 \
  -- uvx cshel-image-tools
```

(Run `gcloud auth application-default login` once on the same machine.)

## Verify it loaded

```bash
claude mcp list
```

You should see `cshel-image-tools` and four tools: `generate_image`, `edit_image`, `compose_images`, `upscale_image`.

## Try it from a chat

> "Generate a 16:9 photo of a red bicycle leaning on a mustard-yellow wall, late-afternoon light."
>
> "Now edit that image to add a tabby cat sitting next to the bike."
>
> "Compose these: ~/Pictures/bike.png and ~/Pictures/beach.jpg — put the bike on the beach at sunset."
>
> "Upscale the previous result to 4K."

## Settings file alternative

If you'd rather edit JSON directly, add this to `~/.claude.json` (or your project-scoped `.mcp.json`):

```json
{
  "mcpServers": {
    "cshel-image-tools": {
      "command": "uvx",
      "args": ["cshel-image-tools"],
      "env": { "GEMINI_API_KEY": "your-key" }
    }
  }
}
```

## Project-scoped install

To bind the server to a single repo, run the same `claude mcp add` command from that repo's root and pass `--scope project`. Claude Code will write a `.mcp.json` at the project root for everyone on the team.
