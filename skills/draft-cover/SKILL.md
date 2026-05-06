---
name: draft-cover
description: Draft a 250-350 word cover letter for a specific application. Argument is an application_id from the Turso `applications` table.
---

# draft-cover

**Argument:** `<application_id>`

## Steps

1. Pull data:
   ```sh
   uv run python -m scripts.skill_helpers application <id>          # JSON
   uv run python -m scripts.skill_helpers resume                     # markdown
   uv run python -m scripts.skill_helpers brief "<company>"          # cached brief or empty
   ```

2. Read `prompts/cover.md` from the repo.

3. Compose using `prompts/cover.md` as the system instruction. Inputs: resume (for context only — do not quote), JD, company, and the brief if non-empty.

4. Output the cover letter in markdown.

5. Suggest `/stop-slop` for polish.

**Required env:** `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`.
