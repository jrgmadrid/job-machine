from __future__ import annotations

import os
import sys

from scripts.db import Application
from scripts.email import send_digest


def main() -> int:
    apps = [
        Application(
            id="gh-acme-1",
            company="Acme",
            role="Backend Engineer",
            url="https://example.com/jobs/1",
            jd=(
                "Build distributed systems for our payments platform. Python and Go. "
                "Series B, fully remote, US/EU friendly."
            ),
            score=5,
            discovered_at="2026-05-06T10:00:00Z",
        ),
        Application(
            id="gh-globex-7",
            company="Globex",
            role="Senior Platform Engineer",
            url="https://example.com/jobs/7",
            jd=(
                "We need someone to lead our Kubernetes migration and own developer "
                "experience for ~80 engineers. Remote-first, mid-stage Series C."
            ),
            score=4,
            discovered_at="2026-05-06T10:00:00Z",
        ),
    ]
    send_digest(
        apps,
        os.environ["RESEND_FROM"],
        os.environ["EMAIL_TO"],
        os.environ["RESEND_API_KEY"],
    )
    print(f"sent digest with {len(apps)} synthetic listings to {os.environ['EMAIL_TO']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
