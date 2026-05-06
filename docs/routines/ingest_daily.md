# Daily Ingest Routine

> Paste this body into the prompt field of a new Claude Code Routine at https://claude.ai/code/routines.

## Routine config

| Field | Value |
|---|---|
| Name | `job-machine ingest (daily)` |
| Schedule | `0 8 * * 1-5` (8am weekdays, your local timezone) |
| Repository | `jrgmadrid/job-machine` (default branch `main`) |
| Cloud env | must inject `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`, `RESEND_API_KEY`, `RESEND_FROM`, `EMAIL_TO`. Optional: `MIN_SCORE` (default `3`). |
| Setup script | leave empty — `uv sync --extra dev` runs via the repo's `.claude/settings.json` SessionStart hook, not the env's setup script (the latter runs before the clone and can't see `pyproject.toml`) |

## Routine prompt body

You are running the daily job-ingest pipeline. The deterministic Python part (fetch, dedupe, prefilter) is in `scripts/ingest.py`; AI scoring is your job; persistence + email is `scripts/persist.py`.

### Step 1 — fetch and prefilter

```sh
uv run python -m scripts.ingest > /tmp/ingest.json
```

The output JSON has these top-level keys:

- `candidate_profile`: the user's base profile merged with any `profile_expansion` row.
- `calibration_examples`: list of `{title, company, score, label}` from past application history (empty if not enough data).
- `listings`: list of prefiltered raw listings (`{source_id, title, company, location, url, description, remote}`).
- `hn_hiring_story_id`, `hn_hiring_cache_hit`, `hn_hiring_raw_comments`: HN "Who is hiring?" parsing inputs.

### Step 2 — parse HN comments (only if `hn_hiring_raw_comments` is non-empty)

For each batch of 5 raw comments, dispatch a Haiku subagent (Task tool, `model=claude-haiku-4-5`):

- **System prompt:** the contents of `prompts/hn_parse.md`.
- **User message:** `{"comments": [<batch>]}` as JSON.
- **Expected output:** JSON array of `{comment_id, company, title, location, remote, url, description_excerpt}`.

Concatenate the parsed batches into one array. Cache the result so next month's run reuses it:

```sh
echo '<concatenated_array_json>' | uv run python -m scripts.cache_hn --story-id <hn_hiring_story_id>
```

Then synthesize each parsed entry into a listing dict (matching the `listings` shape, with `source_id = "hn-<story_id>-<comment_id>"`) and append to the `listings` array you'll score in Step 3.

### Step 3 — score listings via Haiku subagents

For each batch of 10 listings:

- **System prompt** (assembled in this exact order):
  1. Contents of `prompts/score.md`
  2. A blank line, then `## Candidate profile\n` followed by `candidate_profile` from Step 1, JSON-pretty-printed.
  3. If `calibration_examples` is non-empty: a blank line, then `## Calibration examples\n` followed by that array, JSON-pretty-printed.
- **User message:** `{"listings": [<batch>]}` as JSON.
- **Expected output:** JSON array of `{id, score, rationale}`.

If your routine session supports parallel Task-tool dispatch, run scoring batches in parallel. Otherwise serial-batched at 10 listings/batch. (See STOP-Cowork-Parallel in STOPS.md.)

### Step 4 — persist + email

Build a JSON array of `{listing, score, rationale}` (one entry per scored listing — listing is the original object from Step 1, score and rationale are from Step 3). Pipe it to:

```sh
echo '<scored_json>' | uv run python -m scripts.persist
```

`persist.py` filters by `MIN_SCORE`, writes qualifying applications to Turso, and sends a digest email via Resend.

## Notes

- **System prompt assembly:** the score prompt content (file) is the unchanged base; profile and calibration examples are appended at runtime. Do not add "you are a helpful assistant…" preambles.
- **Per-source failure:** `scripts.ingest` already catches per-board HTTP errors and records them in `tracked_boards.last_status`. If `scripts.ingest` itself crashes (network outage, Turso unreachable), abort the run.
- **Anti-slop:** the runbook prohibits direct Anthropic SDK calls anywhere in `scripts/`. All AI in this routine MUST run via the Task tool inside this Claude Code session, never via `import anthropic`.
