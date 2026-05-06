---
name: tailor-resume
description: Tailor the candidate's resume to a specific application's job description. Argument is an application_id from the Turso `applications` table.
---

# tailor-resume

**Argument:** `<application_id>`

## Steps

1. Pull the application and resume:
   ```sh
   uv run python -m scripts.skill_helpers application <id>     # JSON: {company, role, jd, ...}
   uv run python -m scripts.skill_helpers resume                # markdown
   ```

2. Read `prompts/tailor.md` from the repo — that's the system framing.

3. Compose: use the contents of `prompts/tailor.md` as the system instruction; pass the resume and JD as inputs alongside the company name. Generate the tailored resume in markdown.

4. Output the tailored resume to chat.

5. If the user wants prose polish, suggest `/stop-slop` next.

**Required env:** `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`.
