#!/usr/bin/env python3
"""Generate an AI Memory Architecture governance manifest for Cline Memory Bank."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_FILES = (
    "projectBrief.md",
    "productContext.md",
    "activeContext.md",
    "systemPatterns.md",
    "techContext.md",
    "progress.md",
)


def build_manifest() -> dict:
    """Return a conservative governance overlay for Cline's documented Memory Bank layout."""
    return {
        "version": 1,
        "authorities": [
            {"domain": "project-scope", "path": "projectBrief.md"},
            {"domain": "project-progress", "path": "progress.md"},
        ],
        "bookmarks": [],
        "references": [
            {"source": "productContext.md", "target": "projectBrief.md"},
            {"source": "systemPatterns.md", "target": "projectBrief.md"},
            {"source": "techContext.md", "target": "projectBrief.md"},
            {"source": "activeContext.md", "target": "productContext.md"},
            {"source": "activeContext.md", "target": "systemPatterns.md"},
            {"source": "activeContext.md", "target": "techContext.md"},
            {"source": "progress.md", "target": "activeContext.md"},
        ],
        "contradictions": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("memory_bank", help="path to the Cline memory-bank directory")
    parser.add_argument(
        "--output",
        default="memory-integrity.json",
        help="output filename inside the memory-bank directory (default: memory-integrity.json)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing output manifest",
    )
    args = parser.parse_args(argv)

    root = Path(args.memory_bank).resolve()
    if not root.is_dir():
        print(f"ERROR: memory-bank directory not found: {root}")
        return 2

    output_name = Path(args.output)
    if output_name.is_absolute() or len(output_name.parts) != 1 or output_name.name in {"", ".", ".."}:
        print("ERROR: --output must be a filename inside the memory-bank directory")
        return 2

    output = root / output_name
    if output.exists() and not args.force:
        print(f"ERROR: output already exists: {output}; use --force to replace it")
        return 2

    manifest = build_manifest()
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    missing = [name for name in REQUIRED_FILES if not (root / name).is_file()]
    print(f"WROTE: {output}")
    if missing:
        print("NOTE: Cline core files currently missing: " + ", ".join(missing))
        print("Run Memory Integrity Check to surface missing authority/reference findings.")
    else:
        print("FOUND: all six documented Cline core Memory Bank files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
