from __future__ import annotations

import html as html_lib
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any

import httpx

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

_WWR_CATEGORIES = {
    "programming": "remote-programming-jobs",
    "fullstack": "remote-full-stack-programming-jobs",
    "backend": "remote-back-end-programming-jobs",
    "devops": "remote-devops-sysadmin-jobs",
}


@dataclass
class RawListing:
    source_id: str
    title: str
    company: str
    location: str
    url: str
    description: str
    remote: bool = False


def _client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=30.0,
        follow_redirects=True,
    )


def _get_json(url: str) -> Any:
    with _client() as c:
        r = c.get(url)
    r.raise_for_status()
    return r.json()


def _get_text(url: str) -> str:
    with _client() as c:
        r = c.get(url)
    r.raise_for_status()
    return r.text


class _Stripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"p", "br", "li", "div", "h1", "h2", "h3", "h4"}:
            self._parts.append(" ")

    def text(self) -> str:
        return " ".join("".join(self._parts).split())


def _html_to_text(html_in: str) -> str:
    if not html_in:
        return ""
    s = _Stripper()
    s.feed(html_lib.unescape(html_in))
    return s.text()


def _is_remote(*signals: str | bool | None) -> bool:
    for s in signals:
        if isinstance(s, bool) and s:
            return True
        if isinstance(s, str) and "remote" in s.lower():
            return True
    return False


# ---------------------------------------------------------------------------
# Greenhouse
# ---------------------------------------------------------------------------

def fetch_greenhouse(slug: str) -> list[RawListing]:
    data = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")
    listings: list[RawListing] = []
    for j in data.get("jobs", []):
        loc_name = (j.get("location") or {}).get("name") or ""
        metadata_strings = [
            str(m.get("value")) for m in (j.get("metadata") or []) if m.get("value")
        ]
        listings.append(
            RawListing(
                source_id=f"gh-{slug}-{j['id']}",
                title=j["title"],
                company=j.get("company_name") or slug,
                location=loc_name,
                url=j["absolute_url"],
                description=_html_to_text(j.get("content") or ""),
                remote=_is_remote(loc_name, *metadata_strings),
            )
        )
    return listings


# ---------------------------------------------------------------------------
# Ashby
# ---------------------------------------------------------------------------

def fetch_ashby(slug: str) -> list[RawListing]:
    data = _get_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    listings: list[RawListing] = []
    for j in data.get("jobs", []):
        location = j.get("location") or ""
        listings.append(
            RawListing(
                source_id=f"ashby-{slug}-{j['id']}",
                title=j.get("title") or "",
                company=slug,
                location=location,
                url=j.get("applyUrl") or j.get("jobUrl") or "",
                description=_html_to_text(j.get("descriptionHtml") or ""),
                remote=_is_remote(j.get("isRemote"), location),
            )
        )
    return listings


# ---------------------------------------------------------------------------
# Lever
# ---------------------------------------------------------------------------

def fetch_lever(slug: str) -> list[RawListing]:
    postings = _get_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    listings: list[RawListing] = []
    for p in postings:
        cats = p.get("categories") or {}
        location = cats.get("location") or ""
        commitment = cats.get("commitment") or ""
        body = (p.get("description") or "") + " " + (p.get("additional") or "")
        listings.append(
            RawListing(
                source_id=f"lv-{slug}-{p['id']}",
                title=p.get("text") or "",
                company=slug,
                location=location,
                url=p.get("hostedUrl") or p.get("applyUrl") or "",
                description=_html_to_text(body),
                remote=_is_remote(location, commitment),
            )
        )
    return listings


# ---------------------------------------------------------------------------
# Workable — v3 public API requires OAuth (see STOP-Workable in STOPS.md).
# Stub returns []; harvest still records workable boards but ingestion skips them.
# ---------------------------------------------------------------------------

def fetch_workable(slug: str) -> list[RawListing]:
    return []


# ---------------------------------------------------------------------------
# SmartRecruiters
# ---------------------------------------------------------------------------

def fetch_smartrecruiters(slug: str) -> list[RawListing]:
    data = _get_json(
        f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100"
    )
    listings: list[RawListing] = []
    for p in data.get("content", []):
        loc = p.get("location") or {}
        location = ", ".join(
            v for v in (loc.get("city"), loc.get("region"), loc.get("country")) if v
        )
        company = (p.get("company") or {}).get("name") or slug
        listings.append(
            RawListing(
                source_id=f"sr-{slug}-{p['id']}",
                title=p.get("name") or "",
                company=company,
                location=location,
                url=p.get("ref") or f"https://jobs.smartrecruiters.com/{slug}/{p['id']}",
                description="",  # full JD requires a per-posting fetch
                remote=_is_remote(loc.get("remote"), location),
            )
        )
    return listings


# ---------------------------------------------------------------------------
# Recruitee
# ---------------------------------------------------------------------------

def fetch_recruitee(slug: str) -> list[RawListing]:
    data = _get_json(f"https://{slug}.recruitee.com/api/offers/")
    listings: list[RawListing] = []
    for o in data.get("offers", []):
        locs = o.get("locations") or []
        location = ", ".join(loc.get("name", "") for loc in locs if loc.get("name"))
        listings.append(
            RawListing(
                source_id=f"rc-{slug}-{o['id']}",
                title=o.get("title") or o.get("position") or "",
                company=o.get("company_name") or slug,
                location=location,
                url=o.get("careers_apply_url") or o.get("careers_url") or "",
                description=_html_to_text(o.get("description") or ""),
                remote=_is_remote(o.get("remote"), location),
            )
        )
    return listings


# ---------------------------------------------------------------------------
# Remotive (aggregator)
# ---------------------------------------------------------------------------

def fetch_remotive(category: str = "software-dev") -> list[RawListing]:
    data = _get_json(
        f"https://remotive.com/api/remote-jobs?category={category}&limit=100"
    )
    listings: list[RawListing] = []
    for j in data.get("jobs", []):
        listings.append(
            RawListing(
                source_id=f"remotive-{j['id']}",
                title=j.get("title") or "",
                company=j.get("company_name") or "",
                location=j.get("candidate_required_location") or "Remote",
                url=j.get("url") or "",
                description=_html_to_text(j.get("description") or ""),
                remote=True,
            )
        )
    return listings


# ---------------------------------------------------------------------------
# WeWorkRemotely RSS
# ---------------------------------------------------------------------------

def fetch_wwr(category: str) -> list[RawListing]:
    slug = _WWR_CATEGORIES.get(category, category)
    text = _get_text(f"https://weworkremotely.com/categories/{slug}.rss")
    root = ET.fromstring(text)
    listings: list[RawListing] = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()
        region = (item.findtext("region") or "").strip()
        guid = (item.findtext("guid") or link).strip()
        company, _, role = title.partition(":")
        company_str = company.strip() or "Unknown"
        role_str = role.strip() or title
        identifier = guid.rstrip("/").split("/")[-1] or guid
        listings.append(
            RawListing(
                source_id=f"wwr-{identifier}",
                title=role_str,
                company=company_str,
                location=region or "Remote",
                url=link,
                description=_html_to_text(description),
                remote=True,
            )
        )
    return listings


# ---------------------------------------------------------------------------
# HN Algolia (tags=job)
# ---------------------------------------------------------------------------

def fetch_hn_jobs() -> list[RawListing]:
    data = _get_json("https://hn.algolia.com/api/v1/search?tags=job&hitsPerPage=100")
    listings: list[RawListing] = []
    for h in data.get("hits", []):
        title = h.get("title") or ""
        company, _, _ = title.partition(" is hiring")
        listings.append(
            RawListing(
                source_id=f"hnjobs-{h['objectID']}",
                title=title,
                company=(company or "Unknown").strip(),
                location="",
                url=h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                description=h.get("story_text") or "",
                remote=_is_remote(title),
            )
        )
    return listings


# ---------------------------------------------------------------------------
# HN "Who is hiring?" raw fetcher (parsing happens via Haiku subagent later)
# ---------------------------------------------------------------------------

def fetch_hn_hiring_raw() -> tuple[str, list[dict[str, Any]]]:
    """Find the most recent 'Ask HN: Who is hiring?' story; return (story_id, raw children).

    The routine pipes children to a Haiku subagent with prompts/hn_parse.md to extract listings.
    """
    search = _get_json(
        "https://hn.algolia.com/api/v1/search_by_date?"
        "query=Ask+HN%3A+Who+is+hiring&tags=story&"
        "restrictSearchableAttributes=title&hitsPerPage=10"
    )
    story_id = ""
    for hit in search.get("hits", []):
        title = (hit.get("title") or "").lower()
        if "who is hiring" in title and "ask hn" in title:
            story_id = str(hit["objectID"])
            break
    if not story_id:
        return "", []
    item = _get_json(f"https://hn.algolia.com/api/v1/items/{story_id}")
    return story_id, item.get("children") or []


def serialize_listings(listings: list[RawListing]) -> str:
    return json.dumps([listing.__dict__ for listing in listings])


def deserialize_listings(payload: str) -> list[RawListing]:
    return [RawListing(**row) for row in json.loads(payload)]
