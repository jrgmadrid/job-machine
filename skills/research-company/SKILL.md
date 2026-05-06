---
name: research-company
description: Produce a 200-400 word interview-prep brief on a company. Argument is a company name OR an application_id. Reuses cached briefs when fresh; refreshes via WebSearch otherwise.
---

# research-company

**Argument:** `<company_name>` OR `<application_id>`

## Steps

1. Resolve the company name:
   ```sh
   uv run python -m scripts.skill_helpers company-from <arg>
   ```
   If `<arg>` is an application_id, this prints the row's `company`; otherwise it echoes the arg.

2. Check the cache:
   ```sh
   uv run python -m scripts.skill_helpers brief "<company>"
   ```
   Non-empty → that's the brief. Output to chat and stop.

3. Empty → read `prompts/research.md` from the repo. Use WebFetch / WebSearch to gather: company homepage, recent news (Crunchbase, news sites), engineering culture (their tech blog if any). Synthesize per the schema in `research.md`.

4. Save the brief to Turso for next time:
   ```sh
   echo '<brief_markdown>' | uv run python -m scripts.skill_helpers save-brief "<company>"
   ```

5. Output the brief to chat.

**Required env:** `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`.
