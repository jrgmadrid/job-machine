# STOPS

Blockers and informational deviations from spec. Append new entries at the bottom.

## STOP-0 — `.env` missing
Phase: 0
Question: Provide values for `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`, `RESEND_API_KEY`, `RESEND_FROM`, `EMAIL_TO`.
Default if unanswered: `.env.example` scaffolded; Phase 2 (live DB bootstrap), Phase 3 (smoke email), Phase 4 acceptance (b) (Turso writes), and Phase 8 (end-to-end) deferred until present.
Cost of waiting: deterministic Python work and prompt drafting proceeds; live smoke tests blocked.

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
