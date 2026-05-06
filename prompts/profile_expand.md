# Profile expansion

Expand the candidate's base profile into search-friendly terms for job-board harvest.

Input (appended at runtime):
- `profile`: JSON with role, seniority, target_segments, avoid, location_preference, etc.

Output: JSON object with these keys:
- `expanded_keywords`: list[str] — synonyms and adjacent role titles
- `target_segments`: list[str] — industries / company stages worth pursuing
- `excluded_segments`: list[str] — industries / domains to skip
- `search_query_terms`: list[str] — short phrases for `site:` searches against ATS hosts

Rules:
- 8-15 entries per list.
- Lowercased, deduplicated.
- No marketing fluff ("rockstar", "ninja", "wizard").
- Return only the JSON object.
