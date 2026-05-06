"""Daily ingest step 3: read scored listings JSON from stdin, persist, send digest."""
from __future__ import annotations

import json
import os
import sys

from scripts.db import Application, Database
from scripts.email import send_digest


def main() -> int:
    payload = json.load(sys.stdin)
    min_score = int(os.environ.get("MIN_SCORE", "3"))
    db = Database.from_env()

    qualifying: list[Application] = []
    for entry in payload:
        if entry["score"] < min_score:
            continue
        listing = entry["listing"]
        app = Application(
            id=listing["source_id"],
            company=listing["company"],
            role=listing["title"],
            url=listing["url"],
            jd=listing.get("description") or None,
            score=entry["score"],
            notes=entry.get("rationale"),
        )
        db.add(app)
        qualifying.append(app)

    if qualifying:
        send_digest(
            qualifying,
            os.environ["RESEND_FROM"],
            os.environ["EMAIL_TO"],
            os.environ["RESEND_API_KEY"],
        )
        db.mark_emailed([a.id for a in qualifying])

    print(
        f"persisted {len(qualifying)} qualifying application"
        f"{'s' if len(qualifying) != 1 else ''}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
