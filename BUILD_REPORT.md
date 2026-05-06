# BUILD_REPORT

> Sanitized summary of the autonomous build session. Committed for posterity.

## Phases completed

| Phase | Status | Notes |
|---|---|---|
| 0 — Pre-flight | Partial | Git config + remote + SSH all verified. `.env` missing → STOP-0. `uv` installed during Phase 1. |
| 1 — Repo skeleton + prompts | ✅ | Layout, `pyproject.toml` (libsql>=0.1.11), opsec hook (regex corrected), CI workflow, all 7 prompt files, first commit + push. |
| 2 — Storage layer | ✅ | `scripts/db.py` Database class with 30+ methods, `scripts/schema.sql`, 14 unit tests against ephemeral local libsql. Live Turso bootstrap deferred (STOP-0). |
| 3 — Email layer | ✅ | `scripts/email.py` with opsec gate on RESEND_FROM, plain + inline-styled HTML, smoketest CLI, 8 unit tests. Live send deferred (STOP-0). |
| 4 — Source fetchers | ✅ | 9 live fetchers verified against airbnb / ramp / palantir / visa / intigriti / Remotive / WeWorkRemotely / HN. Workable stubbed (STOP-Workable). detect.py + harvest.py written; Turso writes deferred (STOP-0). |
| 5 — Prompt validation | Partial | Prompts drafted in Phase 1, schema-first, ≤30 lines each. Paste-into-Claude-Code validation by user pending. |
| 6 — Cowork routines | ✅ | 3 routine prompts in `docs/routines/` (per INFO-Cowork-1 pivot). Orchestration glue: `scripts/{ingest,persist,cache_hn,profile_save,harvest}.py`. STOP-Cowork-Parallel pending verification. |
| 7 — Skills | ✅ | 4 SKILL.md files using verified frontmatter format. `scripts/skill_helpers.py` shim. Install via symlink. |
| 8 — End-to-end validation | Partial | `scripts/seed_resume.py` CLI written. `docs/validation.md` skeleton with 7 checkbox sections. Manual triggers gated on STOP-0. |
| 9 — Public artifact polish | Mostly ✅ | README (3 sections per spec, with ASCII architecture diagram), POSTMORTEM (~1850 words, six sections). `gh repo edit` for description + topics requires the user to add `jrgmadrid` as a second `gh auth` account (current default is the other GitHub account on this machine); manual step documented below. |

## STOPS resolved during build

- **INFO-Cowork-1**: routine prompts moved to `docs/routines/` (not `routines/`). Phase 6 acceptance text rewritten.
- **INFO-libsql-1**: pyproject.toml uses `libsql>=0.1.11` (was `libsql-experimental` in runbook).
- **INFO-Hook-Regex-1**: pre-commit hook regex fixed (BRE→ERE alternation; word-boundary anchoring; character-class wrapping for self-commit).
- **INFO-Python-Pin-1**: project pinned to Python 3.12 (libsql 0.1.11 has no cp314 wheel; system has 3.14).

## STOPS still outstanding

- **STOP-0** — `.env` missing. Required: `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`, `RESEND_API_KEY`, `RESEND_FROM`, `EMAIL_TO`. Blocks live tests for Phases 2/3, Phase 4 acceptance (b), and all of Phase 8 manual smoke.
- **STOP-Cowork-Parallel** — verify whether Routines' cloud Claude Code sessions support parallel Task-tool fanout. Default if unverified: serial scoring, batch=10. Latency cost only.
- **STOP-Workable** — public Workable API requires OAuth. Fetcher is stubbed; Workable boards in `tracked_boards` are silently skipped. Possible paths: (a) HTML-scrape (fragile), (b) provide an OAuth token (loses no-auth property), (c) drop Workable from the supported set.

## Validation results

- All 27 unit tests pass.
- All 9 live fetcher tests pass.
- Ruff lint clean across `scripts/`, `tests/`, `docs/`.
- Final opsec sweep: `git log -p` against the hook's regex returns nothing.
- CI green on push (ruff + pytest -m 'not live').

## Things to revisit next iteration

- Bootstrap calibration with synthetic positive/negative examples so the scorer has shots from day one.
- Capture live API responses into `fixtures/` and rewrite parsing tests to run offline; keep `@pytest.mark.live` as on-demand smoke.
- Add `scripts/print_score_prompt.py` to dump the assembled (base + profile + calibration) score prompt for paste-into-Claude dry-runs.
- Consider increasing HN parse batch size from 5 to 20 (Haiku 4.5's larger context).
- Decide on Workable strategy.
- Add CI step that runs `grep -r 'anthropic.Anthropic\|messages.create' scripts/ routines/ skills/` and fails on any hit.

## Manual follow-ups for the user

1. **`gh` repo metadata.** The current `gh auth` is on the other GitHub account, so I couldn't run `gh repo edit jrgmadrid/job-machine ...` from this session. After `gh auth login --hostname github.com` (and selecting `jrgmadrid`), run:
   ```sh
   gh auth switch --user jrgmadrid
   gh repo edit jrgmadrid/job-machine \
     --description "Solo-built job-search pipeline — Claude Code Routines, Turso state, scored Resend digests" \
     --add-topic claude --add-topic agents --add-topic automation --add-topic python
   ```

2. **Provision `.env`** (resolves STOP-0). Create a Turso DB + auth token, a Resend API key, verify a sender domain, then:
   ```sh
   cp .env.example .env  # then fill in real values
   uv run python -m scripts.db bootstrap
   uv run python -m scripts.email_smoketest  # confirm digest delivery
   ```

3. **Seed the resume.** `uv run python -m scripts.seed_resume --file ~/path/to/resume.md`. The resume content stays out of the repo.

4. **Register the three routines** at https://claude.ai/code/routines — paste the body of each file in `docs/routines/` into the prompt field, set the schedule + repo + cloud env per its header table.

5. **First manual triggers, in order:** `profile_monthly` → `harvest_weekly` → `ingest_daily`. Watch the digest land in `EMAIL_TO`.

6. **Symlink the four skills** into `~/.claude/skills/` (snippet in README), then smoke-test each against an application_id from the digest.

7. **Fill in `docs/validation.md`** as you go.

## Time spent

Roughly 4 hours of focused work, matching the runbook's estimate. The biggest time sinks were the pre-commit hook regex correction (BRE/ERE confusion + word-boundary fix) and the live fetcher slug verification (figma is no longer on Lever; bosch has zero open SmartRecruiters roles).
