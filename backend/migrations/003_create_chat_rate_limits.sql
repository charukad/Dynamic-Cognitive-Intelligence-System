CREATE TABLE IF NOT EXISTS chat_request_rate_limits (
    bucket_key CHAR(64) PRIMARY KEY,
    scope VARCHAR(64) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    request_count INTEGER NOT NULL DEFAULT 0,
    limit_value INTEGER NOT NULL,
    window_seconds INTEGER NOT NULL,
    window_started_at TIMESTAMPTZ NOT NULL,
    window_expires_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_request_rate_limits_expires_at
    ON chat_request_rate_limits(window_expires_at);

CREATE INDEX IF NOT EXISTS idx_chat_request_rate_limits_scope_subject
    ON chat_request_rate_limits(scope, subject);
