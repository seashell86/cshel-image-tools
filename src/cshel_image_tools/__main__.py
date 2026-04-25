"""CLI entry point. Default action runs the MCP server; subcommands handle setup."""

from __future__ import annotations

import argparse
import sys

from cshel_image_tools import __version__
from cshel_image_tools.config import user_config_paths
from cshel_image_tools.server import run

STARTER_ENV = """\
# cshel-image-tools per-user config. Loaded automatically by the server
# regardless of the directory it is launched from. Process env still wins.

# --- Pick ONE auth path ---
GEMINI_API_KEY=

# GOOGLE_GENAI_USE_VERTEXAI=true
# GOOGLE_CLOUD_PROJECT=
# GOOGLE_CLOUD_LOCATION=us-central1

# --- Optional ---
# CSHEL_IMAGE_OUTPUT_DIR=~/Pictures/nano-banana
# CSHEL_IMAGE_DEFAULT_RESOLUTION=2K
# CSHEL_IMAGE_SAFETY=standard
"""


def _cmd_init(_: argparse.Namespace) -> int:
    target = user_config_paths()[0]
    if target.exists():
        print(f"Already exists: {target}", file=sys.stderr)
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(STARTER_ENV)
    target.chmod(0o600)
    print(f"Wrote starter config to {target}")
    print("Edit it to add your GEMINI_API_KEY (or Vertex AI vars), then start any MCP client.")
    return 0


def _cmd_where(_: argparse.Namespace) -> int:
    for p in user_config_paths():
        marker = "exists" if p.is_file() else "not found"
        print(f"{p}  [{marker}]")
    return 0


def _cmd_serve(_: argparse.Namespace) -> int:
    run()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cshel-image-tools",
        description=(
            "MCP server for Google's Nano Banana Pro (Gemini 3 Pro Image). "
            "With no subcommand, runs the server over stdio."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="cmd")

    p_serve = sub.add_parser("serve", help="Run the MCP server (default)")
    p_serve.set_defaults(func=_cmd_serve)

    p_init = sub.add_parser(
        "init",
        help=(
            "Create a starter per-user config file at "
            "~/.config/cshel-image-tools/.env so every MCP client picks up your key."
        ),
    )
    p_init.set_defaults(func=_cmd_init)

    p_where = sub.add_parser("where", help="Print the per-user config paths the server checks")
    p_where.set_defaults(func=_cmd_where)

    args = parser.parse_args(argv)
    func = getattr(args, "func", _cmd_serve)
    return func(args)


if __name__ == "__main__":
    raise SystemExit(main())
