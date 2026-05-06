from __future__ import annotations

import pytest

from scripts.fetchers import (
    RawListing,
    _html_to_text,
    _is_remote,
    deserialize_listings,
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
    serialize_listings,
)


def test_html_to_text() -> None:
    assert _html_to_text("<p>hello <b>world</b></p>") == "hello world"
    assert _html_to_text("Foo &amp; bar") == "Foo & bar"
    assert _html_to_text("") == ""


def test_is_remote_signals() -> None:
    assert _is_remote(True) is True
    assert _is_remote("Remote, US") is True
    assert _is_remote("San Francisco") is False
    assert _is_remote(None, "") is False
    assert _is_remote(False, "remote-only") is True


def test_serialize_roundtrip() -> None:
    lst = [
        RawListing(
            source_id="gh-acme-1",
            title="Backend",
            company="Acme",
            location="Remote",
            url="https://example.com/1",
            description="x",
            remote=True,
        )
    ]
    assert deserialize_listings(serialize_listings(lst)) == lst


def test_workable_returns_empty() -> None:
    assert fetch_workable("anything") == []


@pytest.mark.live
def test_greenhouse_live() -> None:
    listings = fetch_greenhouse("airbnb")
    assert len(listings) > 0
    sample = listings[0]
    assert sample.source_id.startswith("gh-airbnb-")
    assert sample.title and sample.url


@pytest.mark.live
def test_ashby_live() -> None:
    listings = fetch_ashby("ramp")
    assert len(listings) > 0
    assert listings[0].source_id.startswith("ashby-ramp-")


@pytest.mark.live
def test_lever_live() -> None:
    listings = fetch_lever("palantir")
    assert len(listings) > 0
    assert listings[0].source_id.startswith("lv-palantir-")


@pytest.mark.live
def test_smartrecruiters_live() -> None:
    listings = fetch_smartrecruiters("visa")
    assert len(listings) > 0
    assert listings[0].source_id.startswith("sr-visa-")


@pytest.mark.live
def test_recruitee_live() -> None:
    listings = fetch_recruitee("intigriti")
    assert len(listings) > 0
    assert listings[0].source_id.startswith("rc-intigriti-")


@pytest.mark.live
def test_remotive_live() -> None:
    listings = fetch_remotive("software-dev")
    assert len(listings) > 0
    assert listings[0].source_id.startswith("remotive-")
    assert listings[0].remote


@pytest.mark.live
def test_wwr_live() -> None:
    listings = fetch_wwr("programming")
    assert len(listings) > 0
    assert listings[0].source_id.startswith("wwr-")
    assert listings[0].remote


@pytest.mark.live
def test_hn_jobs_live() -> None:
    listings = fetch_hn_jobs()
    assert len(listings) > 0
    assert listings[0].source_id.startswith("hnjobs-")


@pytest.mark.live
def test_hn_hiring_raw_live() -> None:
    story_id, comments = fetch_hn_hiring_raw()
    assert story_id
    assert isinstance(comments, list)
    assert len(comments) > 0
