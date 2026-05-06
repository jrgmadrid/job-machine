# Monthly Profile-Expand Routine

> Paste this body into a new Claude Code Routine at https://claude.ai/code/routines.

## Routine config

| Field | Value |
|---|---|
| Name | `job-machine profile-expand (monthly)` |
| Schedule | `0 5 1 * *` (1st of month, 5am, your local timezone) |
| Repository | `jrgmadrid/job-machine` |
| Cloud env | must inject `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`. |
| Setup script | `uv sync` |

## Routine prompt body

Refresh the candidate's profile expansion (synonyms, target segments, search query terms) using Opus.

### Step 1 — load the base profile

```sh
cat config.json
```

Capture the JSON object (keys like `role_keywords`, `seniority`, `location_preference`, `target_segments`, etc.).

### Step 2 — invoke Opus subagent

Dispatch one Task-tool subagent with `model=claude-opus-4-7`:

- **System prompt:** the contents of `prompts/profile_expand.md`.
- **User message:** the JSON object from Step 1, pretty-printed.
- **Expected output:** a single JSON object with these exact keys: `expanded_keywords`, `target_segments`, `excluded_segments`, `search_query_terms`. Each is a list of 8-15 deduplicated lowercase strings.

### Step 3 — persist

```sh
echo '<opus_output_json>' | uv run python -m scripts.profile_save
```

`profile_save.py` writes the expansion to the `profile_expansion` table (single-row, primary-key-locked to `id=1`), upserting on conflict.

The next daily ingest run picks up the new expansion automatically; the next weekly harvest run uses the new `expanded_keywords` for `site:` query construction.
