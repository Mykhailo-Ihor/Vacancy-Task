CREATE TABLE IF NOT EXISTS exercises (
    id TEXT PRIMARY KEY,
    client_name TEXT NOT NULL,
    description TEXT NOT NULL,
    due_date TEXT NOT NULL,
    result TEXT,
    comment TEXT,
    token TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);