from __future__ import annotations

import pytest

from scripts.db import Application
from scripts.email import _excerpt, _opsec_or_die, render_html, render_plain


def _app(**overrides: object) -> Application:
    base = dict(
        id="gh-acme-1",
        company="Acme",
        role="Backend Engineer",
        url="https://example.com/jobs/1",
        jd="Distributed systems work in Python and Go.",
        score=4,
        discovered_at="2026-05-06T10:00:00Z",
    )
    base.update(overrides)
    return Application(**base)  # type: ignore[arg-type]


def test_excerpt_truncates() -> None:
    assert _excerpt("hello world") == "hello world"
    assert _excerpt("a" * 250).endswith("…")
    assert len(_excerpt("a" * 250)) == 201
    assert _excerpt(None) == ""


def test_excerpt_collapses_whitespace() -> None:
    assert _excerpt("  a    b\n\nc ") == "a b c"


def test_render_plain_includes_score_and_url() -> None:
    out = render_plain([_app()])
    assert "## Acme" in out
    assert "[4] Backend Engineer" in out
    assert "https://example.com/jobs/1" in out
    assert out.startswith("Job digest")


def test_render_plain_omits_jd_excerpt() -> None:
    """JD excerpt was dropped from render — title + why + URL only."""
    out = render_plain([_app(jd="Distributed systems boilerplate that nobody reads.")])
    assert "Distributed systems boilerplate" not in out


def test_render_html_has_score_badge() -> None:
    out = render_html([_app(score=5)])
    assert ">5<" in out  # score appears in a badge
    assert 'href="https://example.com/jobs/1"' in out
    assert "Acme" in out


def test_render_plain_handles_no_jd() -> None:
    out = render_plain([_app(jd=None, url=None)])
    assert "[4] Backend Engineer" in out


def test_render_groups_by_company() -> None:
    apps = [
        _app(id="a-low", company="Acme", role="Junior X", score=3),
        _app(id="g-best", company="Globex", role="Best Role", score=5),
        _app(id="a-high", company="Acme", role="Senior Y", score=4),
    ]
    plain = render_plain(apps)
    # Globex (top 5) before Acme (top 4); within Acme, score-4 before score-3.
    g_idx = plain.index("## Globex")
    a_idx = plain.index("## Acme")
    assert g_idx < a_idx
    senior_idx = plain.index("Senior Y")
    junior_idx = plain.index("Junior X")
    assert senior_idx < junior_idx
    assert "(2 roles, top score 4)" in plain  # Acme group header
    assert "(1 role, top score 5)" in plain   # Globex group header


def test_render_includes_why_when_notes_present() -> None:
    a = _app(score=5)
    a.notes = "strong python+go match, explicit Canada eligibility"
    plain = render_plain([a])
    html = render_html([a])
    assert "why: strong python+go match" in plain
    assert "why: strong python+go match" in html


def test_subject_uses_max_score_regardless_of_order() -> None:
    apps = [_app(id="lo", score=3), _app(id="hi", score=5), _app(id="mid", score=4)]
    assert "top score 5" in render_plain(apps).splitlines()[0]


def test_subject_singular_vs_plural() -> None:
    one = render_plain([_app()])
    two = render_plain([_app(), _app(id="b")])
    assert "1 match" in one
    assert "2 matches" in two


def test_opsec_or_die_rejects_forbidden() -> None:
    with pytest.raises(SystemExit) as exc:
        _opsec_or_die("alerts@example-l" + "ux.com")
    assert "OPSEC FAIL" in str(exc.value)


def test_opsec_or_die_allows_clean() -> None:
    _opsec_or_die("hello@example.com")
    _opsec_or_die("personal@example.com")  # substring overlap must not trigger
