# job-machine

Personal job-search pipeline. Pulls listings from public ATS APIs (Greenhouse, Ashby, Lever, Workable, SmartRecruiters, Recruitee, Remotive, WeWorkRemotely, Hacker News), scores them via Claude Haiku, and emails a daily digest. Scheduled execution runs as a Claude Code Routine on Anthropic's hosted infrastructure; state lives in Turso; transactional email goes through Resend.

## Status

Under construction. Phase 1 scaffold landed.
