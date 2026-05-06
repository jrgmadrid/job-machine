CREATE TABLE IF NOT EXISTS applications (
    id TEXT PRIMARY KEY,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    url TEXT,
    jd TEXT,
    status TEXT NOT NULL DEFAULT 'discovered',
    score INTEGER,
    notes TEXT,
    next_action TEXT,
    next_action_due TEXT,
    discovered_at TEXT NOT NULL,
    applied_at TEXT,
    phone_screen_at TEXT,
    interview_at TEXT,
    offer_at TEXT,
    rejected_at TEXT,
    withdrawn_at TEXT,
    emailed_at TEXT
);

CREATE TABLE IF NOT EXISTS seen_jobs (
    id TEXT PRIMARY KEY,
    seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tracked_companies (
    name TEXT PRIMARY KEY,
    domain TEXT,
    discovered_via TEXT NOT NULL,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tracked_boards (
    company TEXT PRIMARY KEY,
    board_type TEXT NOT NULL,
    board_slug TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    last_fetched_at TEXT,
    last_status TEXT
);

CREATE TABLE IF NOT EXISTS board_detect_cache (
    domain TEXT PRIMARY KEY,
    result TEXT,
    checked_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS company_research (
    company TEXT PRIMARY KEY,
    brief TEXT NOT NULL,
    researched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS profile_expansion (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    expanded_keywords TEXT NOT NULL,
    target_segments TEXT NOT NULL,
    excluded_segments TEXT NOT NULL,
    search_query_terms TEXT NOT NULL,
    expanded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resume_blob (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    content TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hn_cache (
    story_id TEXT PRIMARY KEY,
    listings_json TEXT NOT NULL,
    cached_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_emailed ON applications(emailed_at, score);
CREATE INDEX IF NOT EXISTS idx_tracked_boards_type ON tracked_boards(board_type);
