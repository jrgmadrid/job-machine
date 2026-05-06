"""Daily ingest step 1: fetch all sources, dedupe, prefilter, output JSON for the routine."""
from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from scripts.db import Application, Database
from scripts.fetchers import (
    RawListing,
    fetch_ashby,
    fetch_greenhouse,
    fetch_hn_hiring_raw,
    fetch_hn_jobs,
    fetch_lever,
    fetch_recruitee,
    fetch_remotive,
    fetch_smartrecruiters,
    fetch_workable,
    fetch_wwr,
)

_REPO_ROOT = Path(__file__).parent.parent
_CONFIG_PATH = _REPO_ROOT / "config.json"

_FETCHER_BY_TYPE = {
    "greenhouse": fetch_greenhouse,
    "ashby": fetch_ashby,
    "lever": fetch_lever,
    "workable": fetch_workable,
    "smartrecruiters": fetch_smartrecruiters,
    "recruitee": fetch_recruitee,
}

_SKIP_TITLE_PATTERN = re.compile(
    r"\b(sales|recruiter|marketing|finance|hr|exec|intern|"
    r"account executive|customer success|legal|compliance|administrative)\b",
    re.IGNORECASE,
)


def _load_profile(db: Database) -> dict[str, Any]:
    base = json.loads(_CONFIG_PATH.read_text())
    expansion = db.get_profile_expansion()
    if expansion:
        base["expanded_keywords"] = expansion.expanded_keywords
        base["target_segments"] = expansion.target_segments
        base["excluded_segments"] = expansion.excluded_segments
    return base


def _is_too_old(posted_at: str | None, max_age_days: int) -> bool:
    """Return True if the listing's `posted_at` is older than the cutoff. None passes through."""
    if not posted_at:
        return False
    try:
        dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return datetime.now(UTC) - dt > timedelta(days=max_age_days)


def prefilter(listings: list[RawListing], profile: dict[str, Any]) -> list[RawListing]:
    avoid_terms = [t.lower() for t in profile.get("avoid", [])]
    excluded_co = {c.lower() for c in profile.get("excluded_companies", [])}
    locations = [loc.lower() for loc in profile.get("location_preference", [])]
    max_age_days = profile.get("max_listing_age_days", 45)
    out: list[RawListing] = []
    for lst in listings:
        if _SKIP_TITLE_PATTERN.search(lst.title):
            continue
        if lst.company.lower() in excluded_co:
            continue
        title_l = lst.title.lower()
        if any(t in title_l for t in avoid_terms):
            continue
        if not lst.remote:
            location_l = lst.location.lower()
            if not any(loc in location_l for loc in locations):
                continue
        if _is_too_old(lst.posted_at, max_age_days):
            continue
        out.append(lst)
    return out


def _calibration_payload(db: Database) -> list[dict[str, Any]]:
    pos, neg = db.calibration_examples()
    if len(pos) < 2 or len(neg) < 2:
        return []
    return [_calibration_entry(a, "good") for a in pos] + [
        _calibration_entry(a, "bad") for a in neg
    ]


def _calibration_entry(app: Application, label: str) -> dict[str, Any]:
    return {
        "title": app.role,
        "company": app.company,
        "score": app.score,
        "label": label,
    }


def _safe_fetch(
    fetcher: Any, slug: str, db: Database, company: str
) -> list[RawListing]:
    try:
        listings = fetcher(slug)
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError) as e:
        db.mark_board_status(company, f"error: {type(e).__name__}: {e}"[:200])
        return []
    db.mark_board_status(company, "ok")
    return listings


def main() -> int:
    db = Database.from_env()
    profile = _load_profile(db)

    all_listings: list[RawListing] = []

    # Global feeds
    all_listings += fetch_remotive("software-dev")
    all_listings += fetch_hn_jobs()
    all_listings += fetch_wwr("programming")
    all_listings += fetch_wwr("backend")

    # Tracked boards
    for board in db.list_tracked_boards():
        fetcher = _FETCHER_BY_TYPE.get(board.board_type)
        if not fetcher:
            continue
        all_listings += _safe_fetch(fetcher, board.board_slug, db, board.company)

    # HN hiring (raw — parsing happens via Haiku subagent in the routine)
    story_id, raw_comments = fetch_hn_hiring_raw()
    cached_listings_json = db.get_hn_cache(story_id) if story_id else None
    if cached_listings_json:
        cached = json.loads(cached_listings_json)
        all_listings += [
            RawListing(
                source_id=f"hn-{story_id}-{c['comment_id']}",
                title=c.get("title", ""),
                company=c.get("company", ""),
                location=c.get("location", ""),
                url=c.get("url") or "",
                description=c.get("description_excerpt", ""),
                remote=bool(c.get("remote")),
            )
            for c in cached
        ]

    # Dedupe
    fresh: list[RawListing] = []
    for lst in all_listings:
        if not db.is_seen(lst.source_id):
            db.mark_seen(lst.source_id)
            fresh.append(lst)

    prefiltered = prefilter(fresh, profile)

    json.dump(
        {
            "candidate_profile": profile,
            "calibration_examples": _calibration_payload(db),
            "listings": [asdict(lst) for lst in prefiltered],
            "hn_hiring_story_id": story_id,
            "hn_hiring_cache_hit": bool(cached_listings_json),
            "hn_hiring_raw_comments": raw_comments if story_id and not cached_listings_json else [],
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
