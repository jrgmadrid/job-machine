"""CLI helper for the monthly profile-expand routine: save Opus-emitted JSON to Turso."""
from __future__ import annotations

import json
import sys

from scripts.db import Database, ProfileExpansion


def main() -> int:
    data = json.load(sys.stdin)
    Database.from_env().save_profile_expansion(
        ProfileExpansion(
            expanded_keywords=data["expanded_keywords"],
            target_segments=data["target_segments"],
            excluded_segments=data["excluded_segments"],
            search_query_terms=data["search_query_terms"],
        )
    )
    print("profile expansion saved", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
