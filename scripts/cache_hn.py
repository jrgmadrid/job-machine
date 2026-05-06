"""CLI helper for the daily ingest routine: cache parsed HN listings keyed by story ID.

Usage:
    cat parsed.json | uv run python -m scripts.cache_hn --story-id 47975571
"""
from __future__ import annotations

import argparse
import sys

from scripts.db import Database


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--story-id", required=True)
    args = parser.parse_args()
    payload = sys.stdin.read()
    Database.from_env().set_hn_cache(args.story_id, payload)
    print(f"cached HN listings for story_id={args.story_id}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
