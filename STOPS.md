# STOPS

Blockers and informational deviations from spec. Append new entries at the bottom.

## STOP-0 — RESOLVED 2026-05-06
Phase: 0
Status:
- **Turso**: `aws-us-west-2` DB live; `python -m scripts.db bootstrap` applied schema (9 tables + 3 indexes).
- **Harvest**: 101 boards across 6 ATS types written to `tracked_boards` (Phase 4 acceptance b satisfied).
- **Resend**: smoke send via `scripts.email_smoketest` accepted by Resend API; 2-listing digest delivered to `EMAIL_TO`.
- **Sender**: `onboarding@resend.dev` (Resend's pre-verified test sender). Acceptable for testing; production should later verify a real-name-owned domain — opsec gate already in `_opsec_or_die()` will hard-stop on forbidden tokens.

## INFO-Cowork-1 — Routine prompts live in `docs/routines/`, not `routines/`
Phase: 6
Reason: Per the Claude Code Routines docs (https://code.claude.com/docs/en/routines), routines are configured in the claude.ai web UI and bound to a Git repo at registration time. They are not loaded from a `routines/` directory in the repo. Naming the directory `routines/` would imply runtime loading. The prompts (paste-into-form reference material) now live in `docs/routines/`.
Acceptance rewrite: Phase 6 acceptance "three routine files exist with valid Cowork config syntax" → "three routine prompt files exist + each registered on claude.ai/code/routines + manual trigger produces expected side effect."

## STOP-Cowork-Parallel — Verify Task-tool parallel subagent dispatch in cloud Routines
Phase: 6
Question: Does a routine's cloud Claude Code session support parallel subagent fan-out (multiple Task-tool calls in one assistant turn) the same way an interactive session does?
Default if unanswered: serial scoring with batch size 10 (~2 min total at typical day's volume).
Cost of waiting: latency cost only; correctness unaffected.

## INFO-libsql-1 — `libsql-experimental` superseded by `libsql`
Phase: 2
Reason: PyPI `libsql-experimental` is deprecated in favor of `libsql` (v0.1.11, Sep 2025). `pyproject.toml` uses `libsql>=0.1.11`.

## INFO-Hook-Regex-1 — Pre-commit hook regex syntax corrected
Phase: 1
Reason: Runbook §Opsec's hook used BRE-style alternation (`\|`) with `grep -iE` (ERE). In ERE the backslash is literal, so the pattern matched a backslash character rather than acting as alternation, and forbidden tokens were silently passed. Three fixes applied: (a) ERE alternation (`|`); (b) each forbidden token wrapped in a single-character class so the script can commit itself without self-matching; (c) anchored with word boundaries (`\b…\b`) to suppress substring false positives — e.g. the common English adjective for "private" no longer trips the hook.

## INFO-Python-Pin-1 — Project pinned to Python 3.12
Phase: 1
Reason: `libsql` v0.1.11 has no prebuilt wheel for Python 3.14 (system default on this machine), and the source build via `maturin` fails. Project pinned to 3.12 via `.python-version`; uv installs 3.12.13 alongside.

## INFO-Cloud-Setup — `uv sync` belongs in a SessionStart hook, not the env setup script
Phase: 6
Reason: Cloud-environment **setup scripts** run before the repo is cloned, so `uv sync --extra dev` exits with `No pyproject.toml found`. Per the Claude Code on Web docs, the canonical place for project-dep installation is a `SessionStart` hook in `.claude/settings.json` committed to the repo (runs after the clone, has access to `pyproject.toml`). The env's "Setup script" field should be left empty (uv is pre-installed in the cloud image). Hook is now in place at `.claude/settings.json`.

## INFO-Harvest-Mojeek — Search backend swapped from DuckDuckGo to Mojeek
Phase: 4
Reason: As of 2026-05-06 the DuckDuckGo HTML endpoint (`https://html.duckduckgo.com/html/`) returns HTTP 202 + the DDG homepage for `site:` queries from any non-browser client (tested both POST and GET, with and without primed cookies). Brave Search returns HTTP 429. Mojeek returns HTTP 200 with usable result URLs that the existing host regex can extract directly. `scripts/harvest.py` now hits `https://www.mojeek.com/search?q=...` instead. The 2-second rate limit is preserved.

## STOP-Workable — Public Workable API requires OAuth
Phase: 4
Question: Is there a path to fetch Workable listings without an account-bound OAuth token?
Default if unanswered: `fetch_workable()` is a stub returning `[]`. `tracked_boards` may still hold workable slugs (harvest can detect them), but the daily ingest skips them. If the user wants Workable coverage, options are: (a) scrape `apply.workable.com/{slug}/` HTML (fragile, ToS-borderline), (b) provide a Workable API key in the env (puts the org behind auth), or (c) drop Workable from the supported set.
Cost of waiting: a non-trivial slice of mid-stage company boards is on Workable; we miss them until resolved.
