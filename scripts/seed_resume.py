"""One-shot CLI to seed the candidate's resume into Turso.

The resume itself is not committed to the repo (opsec). Run this once with the
local resume file path; the content lands in `resume_blob.id=1`.

Usage:
    uv run python -m scripts.seed_resume --file path/to/resume.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.db import Database


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, type=Path, help="Resume markdown file")
    args = parser.parse_args()
    content = args.file.read_text()
    if not content.strip():
        print(f"file is empty: {args.file}", file=sys.stderr)
        return 1
    Database.from_env().save_resume(content)
    print(
        f"saved resume ({len(content)} chars, {content.count(chr(10)) + 1} lines) to Turso",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
