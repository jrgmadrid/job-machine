# Weekly Harvest Routine

> Paste this body into a new Claude Code Routine at https://claude.ai/code/routines.

## Routine config

| Field | Value |
|---|---|
| Name | `job-machine harvest (weekly)` |
| Schedule | `0 6 * * 1` (Monday 6am, your local timezone) |
| Repository | `jrgmadrid/job-machine` |
| Cloud env | must inject `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`. |
| Setup script | `uv sync` |

## Routine prompt body

Discover new company job boards via DuckDuckGo `site:` searches against ATS hosts. No AI; this is purely deterministic.

```sh
uv run python -m scripts.harvest
```

`scripts.harvest`:

1. Loads the candidate profile (with any `profile_expansion` overlay) from Turso, falls back to `config.json`.
2. Builds 6 ATS hosts × first-3 role keywords = 18 search queries.
3. POSTs each query to `https://html.duckduckgo.com/html/` with a 2s sleep between calls.
4. Regex-extracts `(board_type, slug)` from result URLs.
5. Inserts new entries into `tracked_boards` (existing slugs are skipped).

The script prints `added <N> new boards` to stderr on success. If the count is zero for two weeks running, the profile's role keywords may be too narrow — refresh `profile_expansion` (run the monthly routine).
