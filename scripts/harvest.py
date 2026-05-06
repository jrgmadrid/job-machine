from __future__ import annotations

import re
import time
from typing import Any

import httpx

from scripts.db import Database
from scripts.fetchers import USER_AGENT

_DDG_URL = "https://html.duckduckgo.com/html/"

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
    role_terms = profile.get("role_keywords", ["engineer"])[:3]
    location_terms = profile.get("location_preference", ["remote"])
    location_clause = " OR ".join(f'"{loc}"' for loc in location_terms)
    queries = [
        f"site:{host} intitle:{role} ({location_clause})"
        for host in _HOSTS.values()
        for role in role_terms
    ]
    return queries


def harvest(profile: dict[str, Any], db: Database, sleep: float = 2.0) -> int:
    queries = build_queries(profile)
    known_companies = {b.company for b in db.list_tracked_boards()}
    new_boards = 0
    with httpx.Client(
        headers={"User-Agent": USER_AGENT}, timeout=30.0, follow_redirects=True
    ) as c:
        for q in queries:
            time.sleep(sleep)
            r = c.post(_DDG_URL, data={"q": q})
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
