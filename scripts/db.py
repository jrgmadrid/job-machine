from __future__ import annotations

import json
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field, fields
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import libsql

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

_BOARD_CACHE_TTL = timedelta(days=30)
_RESEARCH_TTL = timedelta(days=30)

_TIMESTAMP_COLUMN_FOR_STATUS = {
    "applied": "applied_at",
    "phone_screen": "phone_screen_at",
    "interview": "interview_at",
    "offer": "offer_at",
    "rejected": "rejected_at",
    "withdrawn": "withdrawn_at",
}


@dataclass
class Application:
    id: str
    company: str
    role: str
    url: str | None = None
    jd: str | None = None
    status: str = "discovered"
    score: int | None = None
    notes: str | None = None
    next_action: str | None = None
    next_action_due: str | None = None
    discovered_at: str = ""
    applied_at: str | None = None
    phone_screen_at: str | None = None
    interview_at: str | None = None
    offer_at: str | None = None
    rejected_at: str | None = None
    withdrawn_at: str | None = None
    emailed_at: str | None = None


@dataclass
class BoardRef:
    company: str
    board_type: str
    board_slug: str
    detected_at: str
    last_fetched_at: str | None = None
    last_status: str | None = None


@dataclass
class ProfileExpansion:
    expanded_keywords: list[str] = field(default_factory=list)
    target_segments: list[str] = field(default_factory=list)
    excluded_segments: list[str] = field(default_factory=list)
    search_query_terms: list[str] = field(default_factory=list)
    expanded_at: str = ""


_APP_FIELDS = [f.name for f in fields(Application)]
_BOARD_FIELDS = [f.name for f in fields(BoardRef)]


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _row_to_app(row: tuple[Any, ...]) -> Application:
    return Application(**dict(zip(_APP_FIELDS, row, strict=False)))


def _row_to_board(row: tuple[Any, ...]) -> BoardRef:
    return BoardRef(**dict(zip(_BOARD_FIELDS, row, strict=False)))


class Database:
    def __init__(self, url: str, auth_token: str | None = None) -> None:
        self._url = url
        self._auth_token = auth_token

    @classmethod
    def from_env(cls) -> Database:
        return cls(os.environ["TURSO_DATABASE_URL"], os.environ.get("TURSO_AUTH_TOKEN") or None)

    @contextmanager
    def _connect(self) -> Iterator[Any]:
        conn = (
            libsql.connect(self._url, auth_token=self._auth_token)
            if self._auth_token
            else libsql.connect(self._url)
        )
        try:
            yield conn
        finally:
            conn.close()

    # --- Lifecycle -----------------------------------------------------------

    def bootstrap(self) -> None:
        sql = SCHEMA_PATH.read_text()
        with self._connect() as conn:
            for stmt in (s.strip() for s in sql.split(";") if s.strip()):
                conn.execute(stmt)
            conn.commit()

    # --- Applications --------------------------------------------------------

    def add(self, app: Application) -> None:
        if not app.discovered_at:
            app.discovered_at = _now()
        cols = ", ".join(_APP_FIELDS)
        placeholders = ", ".join("?" for _ in _APP_FIELDS)
        values = tuple(getattr(app, c) for c in _APP_FIELDS)
        with self._connect() as conn:
            conn.execute(f"INSERT INTO applications ({cols}) VALUES ({placeholders})", values)
            conn.commit()

    def get(self, app_id: str) -> Application | None:
        with self._connect() as conn:
            cur = conn.execute(
                f"SELECT {', '.join(_APP_FIELDS)} FROM applications WHERE id = ?",
                (app_id,),
            )
            row = cur.fetchone()
        return _row_to_app(row) if row else None

    def list(self, status: str | None = None) -> list[Application]:
        sql = f"SELECT {', '.join(_APP_FIELDS)} FROM applications"
        params: tuple[Any, ...] = ()
        if status:
            sql += " WHERE status = ?"
            params = (status,)
        sql += " ORDER BY discovered_at DESC"
        with self._connect() as conn:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
        return [_row_to_app(r) for r in rows]

    def update_status(self, app_id: str, status: str) -> None:
        ts_col = _TIMESTAMP_COLUMN_FOR_STATUS.get(status)
        with self._connect() as conn:
            if ts_col:
                conn.execute(
                    f"UPDATE applications SET status = ?, {ts_col} = ? WHERE id = ?",
                    (status, _now(), app_id),
                )
            else:
                conn.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))
            conn.commit()

    def append_note(self, app_id: str, note: str) -> None:
        stamp = f"[{_now()}] {note}"
        with self._connect() as conn:
            conn.execute(
                "UPDATE applications SET notes = COALESCE(notes || char(10), '') || ? WHERE id = ?",
                (stamp, app_id),
            )
            conn.commit()

    def set_action(self, app_id: str, action: str, due: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE applications SET next_action = ?, next_action_due = ? WHERE id = ?",
                (action, due, app_id),
            )
            conn.commit()

    def set_jd(self, app_id: str, jd: str) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE applications SET jd = ? WHERE id = ?", (jd, app_id))
            conn.commit()

    def mark_emailed(self, app_ids: list[str]) -> None:
        if not app_ids:
            return
        ts = _now()
        placeholders = ", ".join("?" for _ in app_ids)
        with self._connect() as conn:
            conn.execute(
                f"UPDATE applications SET emailed_at = ? WHERE id IN ({placeholders})",
                (ts, *app_ids),
            )
            conn.commit()

    def get_unemailed(self, min_score: int) -> list[Application]:
        with self._connect() as conn:
            cur = conn.execute(
                f"SELECT {', '.join(_APP_FIELDS)} FROM applications "
                "WHERE emailed_at IS NULL AND score IS NOT NULL AND score >= ? "
                "ORDER BY score DESC, discovered_at DESC",
                (min_score,),
            )
            rows = cur.fetchall()
        return [_row_to_app(r) for r in rows]

    def needs_followup(self, days: int = 14) -> list[Application]:
        cutoff_dt = (datetime.now(UTC) - timedelta(days=days)).replace(microsecond=0)
        cutoff = cutoff_dt.isoformat().replace("+00:00", "Z")
        with self._connect() as conn:
            cur = conn.execute(
                f"SELECT {', '.join(_APP_FIELDS)} FROM applications "
                "WHERE status IN ('applied', 'phone_screen', 'interview') "
                "AND COALESCE(applied_at, '') < ? "
                "AND offer_at IS NULL AND rejected_at IS NULL AND withdrawn_at IS NULL",
                (cutoff,),
            )
            rows = cur.fetchall()
        return [_row_to_app(r) for r in rows]

    def actions_due(self) -> list[Application]:
        today = _now()[:10]
        with self._connect() as conn:
            cur = conn.execute(
                f"SELECT {', '.join(_APP_FIELDS)} FROM applications "
                "WHERE next_action_due IS NOT NULL AND next_action_due <= ? "
                "ORDER BY next_action_due ASC",
                (today,),
            )
            rows = cur.fetchall()
        return [_row_to_app(r) for r in rows]

    # --- Dedupe --------------------------------------------------------------

    def is_seen(self, source_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("SELECT 1 FROM seen_jobs WHERE id = ?", (source_id,))
            return cur.fetchone() is not None

    def mark_seen(self, source_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO seen_jobs (id, seen_at) VALUES (?, ?)",
                (source_id, _now()),
            )
            conn.commit()

    # --- Companies / boards --------------------------------------------------

    def record_company(self, name: str, domain: str | None, discovered_via: str) -> None:
        ts = _now()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO tracked_companies "
                "(name, domain, discovered_via, first_seen_at, last_seen_at) "
                "VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(name) DO UPDATE SET last_seen_at = excluded.last_seen_at",
                (name, domain, discovered_via, ts, ts),
            )
            conn.commit()

    def record_board(self, company: str, board_type: str, board_slug: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO tracked_boards (company, board_type, board_slug, detected_at) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(company) DO UPDATE SET "
                "board_type = excluded.board_type, board_slug = excluded.board_slug",
                (company, board_type, board_slug, _now()),
            )
            conn.commit()

    def list_tracked_boards(self, board_type: str | None = None) -> list[BoardRef]:
        sql = f"SELECT {', '.join(_BOARD_FIELDS)} FROM tracked_boards"
        params: tuple[Any, ...] = ()
        if board_type:
            sql += " WHERE board_type = ?"
            params = (board_type,)
        with self._connect() as conn:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
        return [_row_to_board(r) for r in rows]

    def mark_board_status(self, company: str, last_status: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE tracked_boards SET last_fetched_at = ?, last_status = ? WHERE company = ?",
                (_now(), last_status, company),
            )
            conn.commit()

    # --- Caches --------------------------------------------------------------

    def get_board_cache(self, domain: str) -> str | None:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT result, checked_at FROM board_detect_cache WHERE domain = ?",
                (domain,),
            )
            row = cur.fetchone()
        if not row:
            return None
        result, checked_at = row
        if datetime.now(UTC) - _parse_iso(checked_at) > _BOARD_CACHE_TTL:
            return None
        return result

    def set_board_cache(self, domain: str, result: str | None) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO board_detect_cache (domain, result, checked_at) VALUES (?, ?, ?) "
                "ON CONFLICT(domain) DO UPDATE SET "
                "result = excluded.result, checked_at = excluded.checked_at",
                (domain, result, _now()),
            )
            conn.commit()

    def get_hn_cache(self, story_id: str) -> str | None:
        with self._connect() as conn:
            cur = conn.execute("SELECT listings_json FROM hn_cache WHERE story_id = ?", (story_id,))
            row = cur.fetchone()
        return row[0] if row else None

    def set_hn_cache(self, story_id: str, listings_json: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO hn_cache (story_id, listings_json, cached_at) VALUES (?, ?, ?) "
                "ON CONFLICT(story_id) DO UPDATE SET "
                "listings_json = excluded.listings_json, cached_at = excluded.cached_at",
                (story_id, listings_json, _now()),
            )
            conn.commit()

    # --- Profile / resume ----------------------------------------------------

    def save_profile_expansion(self, expansion: ProfileExpansion) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO profile_expansion "
                "(id, expanded_keywords, target_segments, excluded_segments, "
                "search_query_terms, expanded_at) "
                "VALUES (1, ?, ?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "expanded_keywords = excluded.expanded_keywords, "
                "target_segments = excluded.target_segments, "
                "excluded_segments = excluded.excluded_segments, "
                "search_query_terms = excluded.search_query_terms, "
                "expanded_at = excluded.expanded_at",
                (
                    json.dumps(expansion.expanded_keywords),
                    json.dumps(expansion.target_segments),
                    json.dumps(expansion.excluded_segments),
                    json.dumps(expansion.search_query_terms),
                    expansion.expanded_at or _now(),
                ),
            )
            conn.commit()

    def get_profile_expansion(self) -> ProfileExpansion | None:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT expanded_keywords, target_segments, excluded_segments, "
                "search_query_terms, expanded_at "
                "FROM profile_expansion WHERE id = 1"
            )
            row = cur.fetchone()
        if not row:
            return None
        return ProfileExpansion(
            expanded_keywords=json.loads(row[0]),
            target_segments=json.loads(row[1]),
            excluded_segments=json.loads(row[2]),
            search_query_terms=json.loads(row[3]),
            expanded_at=row[4],
        )

    def save_resume(self, content: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO resume_blob (id, content, updated_at) VALUES (1, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "content = excluded.content, updated_at = excluded.updated_at",
                (content, _now()),
            )
            conn.commit()

    def get_resume(self) -> str | None:
        with self._connect() as conn:
            cur = conn.execute("SELECT content FROM resume_blob WHERE id = 1")
            row = cur.fetchone()
        return row[0] if row else None

    # --- Research ------------------------------------------------------------

    def save_research(self, company: str, brief: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO company_research (company, brief, researched_at) VALUES (?, ?, ?) "
                "ON CONFLICT(company) DO UPDATE SET "
                "brief = excluded.brief, researched_at = excluded.researched_at",
                (company, brief, _now()),
            )
            conn.commit()

    def get_research(self, company: str, max_age: timedelta = _RESEARCH_TTL) -> str | None:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT brief, researched_at FROM company_research WHERE company = ?",
                (company,),
            )
            row = cur.fetchone()
        if not row:
            return None
        brief, researched_at = row
        if datetime.now(UTC) - _parse_iso(researched_at) > max_age:
            return None
        return brief

    # --- Calibration ---------------------------------------------------------

    def calibration_examples(
        self, n_per_class: int = 3
    ) -> tuple[list[Application], list[Application]]:
        with self._connect() as conn:
            pos_cur = conn.execute(
                f"SELECT {', '.join(_APP_FIELDS)} FROM applications "
                "WHERE status IN ('phone_screen', 'interview', 'offer') "
                "OR (score IS NOT NULL AND score >= 4) "
                "ORDER BY score DESC, discovered_at DESC LIMIT ?",
                (n_per_class,),
            )
            positives = [_row_to_app(r) for r in pos_cur.fetchall()]
            neg_cur = conn.execute(
                f"SELECT {', '.join(_APP_FIELDS)} FROM applications "
                "WHERE status IN ('rejected', 'withdrawn') "
                "OR (score IS NOT NULL AND score <= 2) "
                "ORDER BY discovered_at DESC LIMIT ?",
                (n_per_class,),
            )
            negatives = [_row_to_app(r) for r in neg_cur.fetchall()]
        return positives, negatives


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: python -m scripts.db {bootstrap}", file=sys.stderr)
        return 2
    cmd = args[0]
    if cmd == "bootstrap":
        Database.from_env().bootstrap()
        print("schema applied")
        return 0
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
