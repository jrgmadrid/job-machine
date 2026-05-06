# Resume tailoring

Rewrite the candidate's resume to maximize relevance to a single job description.

Inputs (appended at runtime):
- `resume`: markdown
- `jd`: full text of the job description
- `company`: name

Output: tailored resume in markdown. Same overall structure (Summary, Experience, Skills, Education) as the input.

Rules:
- Reorder bullets so the most relevant ones surface first per role.
- Substitute synonyms where the JD uses different terminology for the same skill.
- Do not invent experience or claim skills not present in the input resume.
- Keep length within 10% of the original.
- Return the markdown directly. No commentary.
