from __future__ import annotations

import os
import tempfile

import pytest

from scripts.db import Application, Database, ProfileExpansion


@pytest.fixture
def db() -> Database:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(path)
    database = Database(path, auth_token=None)
    database.bootstrap()
    yield database
    if os.path.exists(path):
        os.unlink(path)


def test_bootstrap_idempotent(db: Database) -> None:
    db.bootstrap()
    db.bootstrap()


def test_application_roundtrip(db: Database) -> None:
    app = Application(
        id="gh-acme-1",
        company="Acme",
        role="Backend Engineer",
        url="https://example.com/jobs/1",
        score=4,
    )
    db.add(app)

    fetched = db.get("gh-acme-1")
    assert fetched is not None
    assert fetched.company == "Acme"
    assert fetched.score == 4
    assert fetched.discovered_at != ""
    assert fetched.status == "discovered"

    db.update_status("gh-acme-1", "applied")
    after = db.get("gh-acme-1")
    assert after is not None
    assert after.status == "applied"
    assert after.applied_at is not None

    db.append_note("gh-acme-1", "first note")
    db.append_note("gh-acme-1", "second note")
    notes = db.get("gh-acme-1").notes
    assert "first note" in notes and "second note" in notes


def test_list_filters_by_status(db: Database) -> None:
    db.add(Application(id="a", company="A", role="r", status="discovered"))
    db.add(Application(id="b", company="B", role="r", status="applied"))
    assert {a.id for a in db.list()} == {"a", "b"}
    assert [a.id for a in db.list(status="applied")] == ["b"]


def test_unemailed_min_score(db: Database) -> None:
    db.add(Application(id="hi", company="H", role="r", score=5))
    db.add(Application(id="lo", company="L", role="r", score=2))
    db.add(Application(id="ne", company="N", role="r", score=None))

    unemailed = db.get_unemailed(min_score=3)
    assert [a.id for a in unemailed] == ["hi"]

    db.mark_emailed(["hi"])
    assert db.get_unemailed(min_score=3) == []


def test_seen_jobs(db: Database) -> None:
    assert not db.is_seen("src-1")
    db.mark_seen("src-1")
    assert db.is_seen("src-1")
    db.mark_seen("src-1")  # idempotent
    assert db.is_seen("src-1")


def test_tracked_boards(db: Database) -> None:
    db.record_board("acme", "greenhouse", "acme")
    db.record_board("globex", "lever", "globex-co")
    db.record_board("acme", "ashby", "acme-new")  # upsert

    boards = db.list_tracked_boards()
    assert len(boards) == 2
    by_name = {b.company: b for b in boards}
    assert by_name["acme"].board_type == "ashby"
    assert by_name["acme"].board_slug == "acme-new"

    just_lever = db.list_tracked_boards(board_type="lever")
    assert [b.company for b in just_lever] == ["globex"]


def test_board_cache_with_ttl(db: Database) -> None:
    db.set_board_cache("example.com", "greenhouse:example")
    assert db.get_board_cache("example.com") == "greenhouse:example"
    db.set_board_cache("none.com", None)
    assert db.get_board_cache("none.com") is None


def test_hn_cache(db: Database) -> None:
    db.set_hn_cache("story-42", '[{"comment_id": "c1"}]')
    assert db.get_hn_cache("story-42") == '[{"comment_id": "c1"}]'


def test_profile_expansion(db: Database) -> None:
    assert db.get_profile_expansion() is None
    exp = ProfileExpansion(
        expanded_keywords=["backend", "platform", "infra"],
        target_segments=["seed", "series-a"],
        excluded_segments=["agency"],
        search_query_terms=["backend engineer remote"],
    )
    db.save_profile_expansion(exp)
    fetched = db.get_profile_expansion()
    assert fetched is not None
    assert fetched.expanded_keywords == ["backend", "platform", "infra"]
    assert fetched.expanded_at != ""


def test_resume_blob(db: Database) -> None:
    assert db.get_resume() is None
    db.save_resume("# Resume\n\nExperience\n")
    assert db.get_resume() == "# Resume\n\nExperience\n"
    db.save_resume("# Updated")
    assert db.get_resume() == "# Updated"


def test_research_cache(db: Database) -> None:
    assert db.get_research("Acme") is None
    db.save_research("Acme", "Acme makes widgets.")
    assert db.get_research("Acme") == "Acme makes widgets."


def test_calibration_examples(db: Database) -> None:
    db.add(Application(id="p1", company="A", role="r", score=5, status="phone_screen"))
    db.add(Application(id="p2", company="B", role="r", score=4))
    db.add(Application(id="n1", company="C", role="r", score=1, status="rejected"))
    db.add(Application(id="n2", company="D", role="r", score=2))

    pos, neg = db.calibration_examples(n_per_class=5)
    pos_ids = {a.id for a in pos}
    neg_ids = {a.id for a in neg}
    assert "p1" in pos_ids and "p2" in pos_ids
    assert "n1" in neg_ids and "n2" in neg_ids


def test_set_action_and_actions_due(db: Database) -> None:
    db.add(Application(id="a", company="A", role="r"))
    db.set_action("a", "send follow-up", "2020-01-01")
    due = db.actions_due()
    assert [a.id for a in due] == ["a"]
    assert due[0].next_action == "send follow-up"


def test_set_jd(db: Database) -> None:
    db.add(Application(id="a", company="A", role="r"))
    db.set_jd("a", "Job description text.")
    assert db.get("a").jd == "Job description text."
