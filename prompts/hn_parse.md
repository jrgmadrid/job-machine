# HN "Who is hiring?" comment parser

Parse top-level comments from the monthly HN "Ask HN: Who is hiring?" thread into structured listings.

Input (appended at runtime):
- `comments`: list of `{id, text}` (raw comment bodies, batch of up to 5)

Output: JSON array, one entry per parseable listing:

    [{"comment_id": "...", "company": "...", "title": "...", "location": "...", "remote": true, "url": "...", "description_excerpt": "..."}]

Rules:
- Skip comments that aren't job postings (off-topic, replies, meta).
- One comment may yield multiple listings if it lists distinct roles — emit one object per role.
- `description_excerpt`: first 200 chars of the role-specific paragraph, no HTML.
- `url`: application URL if present, else company URL, else `""` (empty string).
- For any missing string field (`company`, `title`, `location`, `url`, `description_excerpt`), emit `""` — never `null`. Downstream code distinguishes empty-string from missing data by length, not nullability.
- Return only the JSON array.
