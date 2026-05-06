# Follow-up email

Draft a brief follow-up email after an application or interview.

Inputs (appended at runtime):
- `application`: `{company, role, status, last_contact_date, notes}`
- `context_hint`: one phrase from the user (e.g., "two weeks since phone screen", "thanks after onsite")

Output: plain-text email body, 80-150 words. No subject line, no signature block.

Rules:
- Open with a one-sentence reference to the specific touchpoint, not "I hope this finds you well."
- Body: one concrete reason this role still interests you, tied to something from prior conversation.
- Close with a clear ask (timeline check, next step).
- Return the plain text directly.
