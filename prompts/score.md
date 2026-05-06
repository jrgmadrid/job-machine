# Job listing scorer

Score each listing 1-5 against the candidate profile (1 = poor fit, 5 = top match).

Inputs (appended at runtime by the routine):
- `candidate_profile`: JSON
- `calibration_examples`: list of `{listing, score, label}` (optional)
- `listings`: list of `{id, title, company, location, url, description, remote}`

Output: JSON array, one entry per input listing, in the same order:

    [{"id": "...", "score": 4, "rationale": "..."}]

Rules:
- Score on overall fit: role match, seniority, tech stack, remote/location, company stage signals.
- Penalize sales/recruiter/marketing/exec/intern titles to ≤2.
- `rationale`: ≤120 chars, factual, no hedging.
- Return only the JSON array. No prose, no code fence.
