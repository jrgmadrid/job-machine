# Company brief

Produce a 200-400 word brief on the company for an interview prep context.

Inputs (appended at runtime):
- `company`: name
- `recent_url_snippets`: search result excerpts the routine pre-fetched (optional)

Output: markdown with sections:

    ## Business
    ## Engineering culture
    ## Recent news
    ## Questions to ask

Rules:
- Each section: 2-5 lines.
- Cite a URL inline only if you actually used it: `[source](url)`.
- Mark unverified claims with "(unverified)".
- Skip sections you can't fill — do not pad.
- Return the markdown directly.
