---
name: draft-followup
description: Draft an 80-150 word follow-up email after applying or interviewing. Arguments are an application_id and an optional one-phrase context hint.
---

# draft-followup

**Arguments:** `<application_id>` `[context_hint]`

`context_hint` is an optional one-phrase description like `"two weeks since phone screen"` or `"thanks after onsite"`.

## Steps

1. Pull the application:
   ```sh
   uv run python -m scripts.skill_helpers application <id>
   ```

2. Read `prompts/followup.md` from the repo.

3. Compose using `followup.md` as the system instruction. Inputs: the application JSON (company, role, status, last_contact_date, notes) plus the `context_hint` if the user provided one.

4. Output a plain-text email body (no subject line, no signature block).

5. Suggest `/stop-slop` for polish.

**Required env:** `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`.
