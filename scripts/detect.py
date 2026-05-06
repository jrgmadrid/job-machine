from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

from scripts.db import Database
from scripts.fetchers import USER_AGENT

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"boards\.greenhouse\.io/([a-z0-9-]+)"), "greenhouse"),
    (re.compile(r"jobs\.lever\.co/([a-z0-9-]+)"), "lever"),
    (re.compile(r"jobs\.ashbyhq\.com/([a-z0-9-]+)"), "ashby"),
    (re.compile(r"apply\.workable\.com/([a-z0-9-]+)"), "workable"),
    (re.compile(r"([a-z0-9-]+)\.recruitee\.com"), "recruitee"),
    (re.compile(r"careers\.smartrecruiters\.com/([a-z0-9-]+)"), "smartrecruiters"),
]

_PROBE_PATHS = ["", "/careers", "/jobs", "/about/careers"]


@dataclass
class DetectedBoard:
    board_type: str
    slug: str


def detect_board(domain: str, company: str, db: Database) -> DetectedBoard | None:
    cached = db.get_board_cache(domain)
    if cached is not None:
        if not cached:
            return None
        board_type, slug = cached.split(":", 1)
        return DetectedBoard(board_type, slug)
    detected = _probe(domain)
    db.set_board_cache(domain, f"{detected.board_type}:{detected.slug}" if detected else "")
    if detected:
        db.record_board(company, detected.board_type, detected.slug)
        db.record_company(company, domain, "detect")
    return detected


def _probe(domain: str) -> DetectedBoard | None:
    with httpx.Client(
        headers={"User-Agent": USER_AGENT}, timeout=15.0, follow_redirects=True
    ) as c:
        for path in _PROBE_PATHS:
            url = f"https://{domain}{path}"
            try:
                r = c.get(url)
            except httpx.HTTPError:
                continue
            if r.status_code != 200:
                continue
            for pattern, board_type in _PATTERNS:
                m = pattern.search(r.text)
                if m:
                    return DetectedBoard(board_type, m.group(1))
    return None
