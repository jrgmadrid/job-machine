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
    assert "[4] Backend Engineer at Acme" in out
    assert "https://example.com/jobs/1" in out
    assert "Distributed systems work" in out
    assert out.startswith("Job digest")


def test_render_html_has_score_badge() -> None:
    out = render_html([_app(score=5)])
    assert ">5<" in out  # score appears in a badge
    assert 'href="https://example.com/jobs/1"' in out
    assert "Acme" in out


def test_render_plain_handles_no_jd() -> None:
    out = render_plain([_app(jd=None, url=None)])
    assert "[4] Backend Engineer at Acme" in out


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
    _opsec_or_die("personal@example.com")  # substring overlap with forbidden tokens must not trigger
