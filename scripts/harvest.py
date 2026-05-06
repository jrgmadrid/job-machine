from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import httpx

from scripts.db import Database
from scripts.fetchers import USER_AGENT

_CONFIG_PATH = Path(__file__).parent.parent / "config.json"

# Mojeek instead of the runbook's DuckDuckGo HTML endpoint — DDG soft-blocks us
# (HTTP 202 + homepage HTML). See INFO-Harvest-Mojeek in STOPS.md.
_SEARCH_URL = "https://www.mojeek.com/search"

_HOSTS = {
    "greenhouse": "boards.greenhouse.io",
    "lever": "jobs.lever.co",
    "ashby": "jobs.ashbyhq.com",
    "workable": "apply.workable.com",
    "recruitee": "recruitee.com",
    "smartrecruiters": "careers.smartrecruiters.com",
}

_HOST_PATTERNS = {
    "greenhouse": re.compile(r"boards\.greenhouse\.io/([a-z0-9-]+)"),
    "lever": re.compile(r"jobs\.lever\.co/([a-z0-9-]+)"),
    "ashby": re.compile(r"jobs\.ashbyhq\.com/([a-z0-9-]+)"),
    "workable": re.compile(r"apply\.workable\.com/([a-z0-9-]+)"),
    "recruitee": re.compile(r"([a-z0-9-]+)\.recruitee\.com"),
    "smartrecruiters": re.compile(r"careers\.smartrecruiters\.com/([a-z0-9-]+)"),
}


def build_queries(profile: dict[str, Any]) -> list[str]:
    """Generate `site:` queries for each ATS host × role keyword.

    Kept deliberately simple (`site:HOST KEYWORD`) — Mojeek rejects (`HTTP 403`)
    queries with `intitle:` operators, parentheses, or boolean OR clauses.
    """
    role_terms = profile.get("role_keywords", ["engineer"])[:3]
    return [f"site:{host} {role}" for host in _HOSTS.values() for role in role_terms]


def _load_profile(db: Database) -> dict[str, Any]:
    base = json.loads(_CONFIG_PATH.read_text())
    expansion = db.get_profile_expansion()
    if expansion:
        base["role_keywords"] = expansion.expanded_keywords[:6] or base.get("role_keywords", [])
    return base


def harvest(profile: dict[str, Any], db: Database, sleep: float = 3.0) -> int:
    queries = build_queries(profile)
    known_companies = {b.company for b in db.list_tracked_boards()}
    new_boards = 0
    with httpx.Client(
        headers={"User-Agent": USER_AGENT}, timeout=30.0, follow_redirects=True
    ) as c:
        for q in queries:
            time.sleep(sleep)
            r = c.get(_SEARCH_URL, params={"q": q})
            r.raise_for_status()
            html = r.text
            for board_type, pattern in _HOST_PATTERNS.items():
                for m in pattern.finditer(html):
                    slug = m.group(1).lower()
                    if slug in known_companies:
                        continue
                    db.record_board(slug, board_type, slug)
                    known_companies.add(slug)
                    new_boards += 1
    return new_boards


def main() -> int:
    db = Database.from_env()
    profile = _load_profile(db)
    new = harvest(profile, db)
    print(f"added {new} new board{'s' if new != 1 else ''}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
