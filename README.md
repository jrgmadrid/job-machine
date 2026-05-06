# job-machine

[![CI](https://github.com/jrgmadrid/job-machine/actions/workflows/ci.yml/badge.svg)](https://github.com/jrgmadrid/job-machine/actions/workflows/ci.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)

## What this is

A solo-built job-search pipeline. Every weekday morning a Claude Code Routine pulls listings from public ATS APIs, scores them against the candidate profile via Haiku subagents, and emails a digest. State lives in Turso (libsql). All AI work — scoring, HN comment parsing, monthly profile expansion — runs as Claude Code subagents inside a Routine cloud session, never via direct Anthropic SDK calls. Four on-demand skills (`tailor-resume`, `draft-cover`, `research-company`, `draft-followup`) cover the rest of the application loop.

## Architecture

```
   ATS public APIs (Greenhouse, Ashby, Lever,        ┌───────────────────────┐
   SmartRecruiters, Recruitee, Remotive,             │  Claude Code Routine  │
   WeWorkRemotely RSS, HN Algolia)                   │  cloud session        │
              │                                      │                       │
              ▼                                      │  ┌─────────────────┐  │
   ┌────────────────────┐                            │  │  Haiku          │  │
   │ scripts/fetchers.py│  ◄──── HTTP, deterministic │  │  subagents      │  │
   │ scripts/ingest.py  │        (no AI, no SDK)     │  │  (scorer,       │  │
   │ scripts/harvest.py │                            │  │  HN parser)     │  │
   └────────────────────┘                            │  └─────────────────┘  │
              │                                      │            │          │
              ▼                                      │            ▼          │
       Turso (libsql)  ◄─────────────────────────────┤    scripts/persist.py │
       applications,                                 │    → Resend digest    │
       seen_jobs,                                    └───────────────────────┘
       tracked_boards,                                            │
       hn_cache,                                                  ▼
       resume_blob, …                                       EMAIL_TO inbox

   ──── deterministic Python ────  ──── AI via Task-tool subagent ────
```

Source fetching, HTML parsing, RSS, dedupe, prefilter, DB I/O, and email send all live in `scripts/` and are deterministic Python. AI work is invoked only from inside a Claude Code Routine cloud session, via the Task tool. The grep `grep -r 'anthropic.Anthropic\|messages.create' scripts/ routines/ skills/` returns nothing, by design.

## Decisions

- **Why Claude Code Routines over a VPS or GitHub Actions cron.** Routines run as full Claude Code sessions, so the same agent that has prompt-engineering and tool-using polish on my laptop also runs the scheduled pipeline. Spawning Haiku subagents for cheap parallel scoring uses my plan rather than burning per-call API credits. A VPS would need its own AI billing account, monitoring, Python + uv installed, and a retry layer. Routines need none of that.

- **Why Turso over local SQLite.** State has to be reachable from both the cloud routine session and my local Claude Code (so skills like `/tailor-resume <id>` can read the same row the digest came from). Local SQLite would force a manual sync. Turso gives me cheap hosted libsql storage that both sides hit. Free tier is generous for a single-user pipeline.

- **Why subagents over direct SDK calls.** Two reasons. First, plan economics — model invocations from inside a Claude Code session bill against the plan rather than per-call. Second, orchestration stays readable: the routine's Claude session spawns Task subagents inline, the Python modules don't import `anthropic`, and the boundary is enforceable by a single grep.

- **Why `site:`-search for board discovery.** Aggregators are full of stale and fake listings. Most companies publish to the same six ATS hosts. A `site:boards.greenhouse.io intitle:engineer` query against DuckDuckGo gives a fresh slug list with negligible overhead, and the boards I find are first-party.

- **Sources, deliberate exclusions.** Greenhouse, Ashby, Lever, SmartRecruiters, Recruitee, Remotive, WeWorkRemotely RSS, and HN Algolia are all unauthenticated public APIs returning real-time data. Workable v3 requires OAuth — stubbed pending a public path (see `STOPS.md`). LinkedIn is ToS-hostile and CAPTCHA-fragile. Indeed has no public API. Adzuna's quality is poor enough that ingesting it is a net negative.

## Installing the skills

```sh
git clone git@github.com:jrgmadrid/job-machine.git
cd job-machine
uv sync --extra dev

# Symlink each skill into your Claude Code skills directory:
for s in tailor-resume draft-cover research-company draft-followup; do
  ln -sf "$(pwd)/skills/$s" "$HOME/.claude/skills/$s"
done

ls ~/.claude/skills | grep -E '(tailor-resume|draft-cover|research-company|draft-followup)'
```

For prose polish on any skill output, invoke the community `/stop-slop` skill.

## Running the routines

The three routines live as paste-into-form prompts in `docs/routines/`. Register each at https://claude.ai/code/routines, point at this repo, set the schedule, and inject env vars per the routine's header table.

## License

MIT — see [LICENSE](LICENSE).
