# End-to-end validation

Sanitized record of the manual smoke-tests that prove the full pipeline works. Fill in checkboxes and counts as each step passes; record only sanitized findings (no real listings, no real company names from the actual job search).

Run on: `<date>`

## Environment

- Cloud routine Python: `<3.12.x>` (cloud Routines provision their own interpreter)
- Local Python: `3.12.13` (project pinned via `.python-version`)
- Turso region: `<aws-us-east-1, etc.>`
- `RESEND_FROM` domain verified (SPF + DKIM): `yes` / `no`
- `EMAIL_TO` configured: `yes` / `no`

## Phase-by-phase smoke

### Phase 2 — schema bootstrap
- [ ] `uv run python -m scripts.db bootstrap` exits 0 against Turso (re-runnable, idempotent)
- [ ] All 10 tables present (`applications`, `seen_jobs`, `tracked_companies`, `tracked_boards`, `board_detect_cache`, `company_research`, `profile_expansion`, `resume_blob`, `hn_cache`, plus indexes)

### Phase 3 — Resend smoke
- [ ] `uv run python -m scripts.email_smoketest` sent
- [ ] Email arrived in `EMAIL_TO`
- [ ] SPF + DKIM both PASS (Gmail → "Show original")
- [ ] HTML renders on mobile (iOS Mail, Gmail web)

### Phase 4 — live fetcher smoke
- [ ] `uv run pytest -m live tests/test_fetchers.py -v` → 9 passed
- [ ] (when STOP-0 resolved) `uv run python -m scripts.harvest` populates `tracked_boards` ≥ 10 entries

### Phase 6 — routine smoke (after registering each on claude.ai/code/routines)
- [ ] `profile_monthly` manual trigger → row written to `profile_expansion`; `expanded_keywords` length: `<N>`
- [ ] `harvest_weekly` manual trigger → `tracked_boards` count delta: `<before> → <after>`
- [ ] `ingest_daily` manual trigger → digest email arrived; listings: `<N>`; top score: `<N>`

### Phase 7 — skills smoke
Pick one application_id from the digest. For each:
- [ ] `/tailor-resume <id>` → resume markdown, ≤10% length delta from base resume
- [ ] `/draft-cover <id>` → 250-350 word markdown cover letter
- [ ] `/research-company <id>` → 200-400 word sectioned brief; cached on second call
- [ ] `/draft-followup <id> "two weeks since phone screen"` → 80-150 word plain-text body

### Final opsec gate
- [ ] Sweep full history with the regex defined in `.pre-commit-hook.sh`:
      `git log -p | grep -iE "$(grep -oE "'[^']+'" .pre-commit-hook.sh | head -1 | tr -d \"'\")"`
      → returns nothing

## Counts (sanitized)

| Table | Rows |
|---|---|
| applications | `<N>` |
| applications by status | discovered=`<N>`, applied=`<N>`, phone_screen=`<N>`, interview=`<N>`, offer=`<N>`, rejected=`<N>`, withdrawn=`<N>` |
| seen_jobs | `<N>` |
| tracked_boards | `<N>` |
| tracked_boards by type | greenhouse=`<N>`, ashby=`<N>`, lever=`<N>`, smartrecruiters=`<N>`, recruitee=`<N>`, workable=`<N>` |
| company_research | `<N>` |
| hn_cache | `<N>` |

## Findings

Open observations, prompts that misbehaved, sources that returned junk, anything to improve. Sanitized — no real names.

-
