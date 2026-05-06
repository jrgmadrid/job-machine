# job-machine: notes from the build

I built job-machine over a weekend in early May 2026 — a scheduled pipeline that scrapes public ATS APIs every weekday morning, scores listings via Haiku subagents, and emails me a digest. Four on-demand skills cover the rest of the application loop. Here's what I learned, what surprised me, and what I'd do differently.

## The reframe: discovery is a side-effect of broad ingestion

The trap I almost fell into was treating discovery as its own AI problem. The first sketch had an "agent that finds new companies hiring people like me." A search agent. A ranker. Maybe a research agent that builds dossiers on each match. All powered by Opus, all expensive, all slow.

The reframe came from a flat observation about how the public job-board ecosystem actually works: most companies that publish to the open web do so on six ATS hosts (Greenhouse, Ashby, Lever, SmartRecruiters, Recruitee, Workable). If you have the per-company slug, you have the API endpoint. There's no inference required to know that `boards-api.greenhouse.io/v1/boards/<slug>/jobs?content=true` returns the company's open roles — that's just the URL.

So discovery becomes ingestion. A `site:boards.greenhouse.io intitle:engineer` query against DuckDuckGo, run weekly, harvests fresh slugs into `tracked_boards`. The daily run iterates them and pulls every posting. Filtering happens twice — once by deterministic regex (drop sales/recruiter/intern roles by title), once by Haiku scoring against my profile. The "AI agent for discovery" got reduced to a six-line CSS-style pattern table and a 2-second-spaced loop. The agent that survived is the scorer, which is doing the only judgment-shaped task in the pipeline: how well does *this* listing actually match *this* candidate?

The lesson: when an AI step looks indispensable, ask whether the deterministic step underneath is genuinely missing or just hidden behind UX. The first version of "AI discovery agent" was hiding a search engine and a regex.

## Source quality: why first-party beats aggregators

The aggregators get pitched as one-stop shops. They're not. Three failure modes show up consistently when you actually ingest from them:

1. **Stale listings.** Companies post and then close roles; aggregators don't always refresh. You end up writing a tailored resume for a JD that's been gone three weeks.
2. **Redirect loops and tracking middleware.** Apply URLs go through four redirects to a partner page that's broken. The first-party board doesn't do this — the apply URL goes to the company's ATS directly.
3. **Fake or hallucinated listings.** Some aggregators now auto-scrape with an LLM and quietly hallucinate location strings, salary ranges, or whole roles. There's no way to detect this from the consumer side.

The first-party ATS APIs are 200-line Python parsers with a known schema, and the data is whatever the company actually published. Easier to debug, easier to trust, and updates within minutes when something changes upstream. The cost is that I had to build the slug-discovery layer myself — but `site:` search turned out to be five lines of regex over DuckDuckGo HTML, and that's the whole layer.

LinkedIn isn't on the source list and won't be. Their ToS is hostile, their bot detection is aggressive, and any scraping path is fragile by design. Indeed has no public API. None of the three are worth the maintenance cost, even at zero.

## Plan vs. API economics

This is the architectural choice I spent the most time on, and it ended up being the cleanest decision in the build.

Direct Anthropic API calls from a VPS would mean: per-call billing, an API key in production env vars, Python SDK round-trips I'd have to monitor and rate-limit and retry. For a single-user pipeline that scores maybe 60 listings a day, the dollar cost is fine — but the operational surface is large for a project that only really needs to do work in 15-minute windows on weekday mornings.

Claude Code Routines run as full Claude Code sessions in Anthropic's cloud, and AI invocations from those sessions bill against my plan rather than per-call. The Task tool spawns subagents (Haiku for scoring, Opus for monthly profile expansion) with model pinning baked in. Once the routine is registered, there's nothing to monitor — Routines retries on failure, env vars come from the cloud-environment config, and the only state I touch is Turso.

The anti-slop rule that nailed this down: `grep -r 'anthropic.Anthropic\|messages.create' scripts/ routines/ skills/` returns nothing. If it ever returns something, the architecture is leaking. That grep belongs in CI's opsec sweep, alongside the forbidden-tokens scan.

## Architecture: deterministic Python + AI orchestration, hard split

The separation that emerged:

- **Deterministic Python** in `scripts/`: source fetching (httpx, no special handling), HTML stripping (stdlib `html.parser`, no `feedparser`, no `BeautifulSoup`), dedupe, prefilter, DB I/O, email send. These functions are pure I/O over typed dataclasses; they don't know LLMs exist.
- **AI orchestration** in `docs/routines/<name>.md`: the routine prompt tells the cloud Claude Code session what to do. It runs the Python steps via shell, dispatches Task-tool subagents for scoring or parsing, then runs more Python to persist.
- **On-demand skills** in `skills/<name>/SKILL.md`: same pattern, invoked from my interactive Claude Code session when I'm applying to a specific role. Each skill loads the application row from Turso, reads the matching `prompts/<x>.md`, and produces output to chat.

Why this split is right: the deterministic part has tests (pytest, 27 unit + 9 `@pytest.mark.live`), runs in CI, and stays the same release-to-release. The orchestration part is markdown — when I want to change scoring behavior, I edit `prompts/score.md` and restart the routine. No deploys, no version-pinning, no "is the AI part out of sync with the Python part" question to debug at 8am.

The one place this gets fuzzy is the boundary between "deterministic prefilter" and "AI scorer." I default to deterministic for things that are unambiguous (drop "Account Executive" by title regex) and AI for things that are noisy (does this Backend Engineer role at a fintech actually look like a fit given my tech stack and target segments?). The deterministic prefilter shrinks ~200 daily listings to ~30; Haiku scores only those. This keeps the AI cost roughly constant at ~30 short calls per day, regardless of how aggressive the harvest layer gets.

## Notes on prompt structure

A few prompt-engineering things worth recording:

- **Schema-first.** Every prompt file in `prompts/` opens with the output schema, before any prose. The score prompt's first non-title line is "JSON array of `{id, score, rationale}`, one per listing, in input order." Models do dramatically better when the schema is the instruction, not an afterthought.
- **No politeness preambles.** The runbook bans "you are a helpful assistant" openers. They waste tokens, train me to write fluffier prompts, and don't measurably help. Each prompt in the repo is ≤30 lines, with the task in ≤2 sentences.
- **Calibration as runtime context, not preamble.** The scorer's `prompts/score.md` is the same on disk forever. The candidate profile and calibration examples (positive/negative past application outcomes) get appended at the routine's runtime. This means the same prompt file works on day one (no calibration) and on day 90 (rich calibration), without any version branching.
- **Prefilter regex is generous.** It's tempting to make the prefilter regex precise. Don't. The cost of an ambiguous role getting scored by Haiku and rejected at score 1 is a fraction of a cent. The cost of accidentally filtering out a genuinely good role is a missed opportunity. The regex skips obvious non-matches; the AI handles the gradient.

## What I'd do differently next time

A few things didn't quite land cleanly:

- **The prompt source-of-truth is virtual.** Right now `prompts/score.md` is a markdown file that the routine session has to assemble at runtime by appending the candidate profile and calibration examples. It works, but it means the "real" system prompt only exists in memory during a routine run. For debugging, I should have written `scripts/print_score_prompt.py` that produces the assembled prompt to stdout so I can paste it into a Claude Code dry-run.
- **The Workable gap.** Workable v3's public API requires OAuth, so my fetcher is a stub returning `[]`. About 15% of relevant boards I've seen in the wild are on Workable. The right fix is probably scraping the public `apply.workable.com/{slug}/` HTML, but that's ToS-borderline; an OAuth-keyed approach loses the "no auth required" property that makes the rest of the source set easy to maintain. I logged a STOP and moved on.
- **HN comment parsing batch size is conservative.** I batched at 5 because I wanted to fit comfortably in one Haiku context window per call. With Haiku 4.5's expanded context I could probably do 20 per batch and quarter the latency. Not worth chasing for monthly cadence, but worth knowing.
- **Calibration bootstrap.** `db.calibration_examples()` feeds positive/negative shots into the scorer once I have application history. Until I've actually applied to a few things, calibration is empty and the scorer runs on raw rules. I should pre-seed the table with a handful of synthetic examples to bootstrap, and revisit how the scorer handles the empty-calibration case.
- **Tests against fixtures, not live APIs.** The `@pytest.mark.live` tests are useful as a smoke check, but they're flaky-by-design (any company can change ATS, any aggregator can rate-limit). For a production maintenance loop, I'd capture each live response once into `fixtures/` and run the parsing tests offline. The live tests would still exist but only run on demand.

## On building in public

This repo is public from the first commit on `@jrgmadrid` because the build itself is the artifact, not just the digests it produces. The pre-commit opsec hook catches forbidden tokens before any commit lands, the README and this post-mortem are explicitly sanitized — no real company names, no political framing, no autobiographical context.

The reason for that constraint is simple: I want this repo to read as engineering judgment, not autobiography. The decisions documented here — deterministic Python under AI orchestration, source-quality over source-quantity, plan-funded subagents over direct SDK — are the parts that matter. The fact that I'm the one running this pipeline against my own job search is incidental to whether the architecture is correct.

If you're reading this and considering a similar pipeline: the discovery-as-ingestion reframe is the leverage. Everything else is plumbing. Build the plumbing well, keep the AI surface narrow, and the system gets out of your way.
