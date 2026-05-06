# Cover letter draft

Draft a 250-350 word cover letter for the candidate applying to the job.

Inputs (appended at runtime):
- `resume`: markdown (for context, not to quote)
- `jd`: full text of the job description
- `company`: name
- `company_brief`: 1-paragraph company summary (optional)

Output: cover letter in markdown.

Rules:
- Three paragraphs: hook (why this role specifically), evidence (one concrete achievement that maps to the JD), close (clear ask).
- No "I am writing to apply for…" opener.
- No "I would be a great fit because…" or other generic closers.
- Specific, not aspirational. Past tense for accomplishments.
- Return the markdown directly.
