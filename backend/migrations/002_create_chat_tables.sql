CREATE TABLE IF NOT EXISTS chat_sessions (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(255) NOT NULL DEFAULT 'New Chat',
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    selected_agent_id VARCHAR(255),
    message_count INTEGER NOT NULL DEFAULT 0,
    last_message_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_status
    ON chat_sessions(status);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_last_message_at
    ON chat_sessions(last_message_at DESC NULLS LAST);

CREATE TABLE IF NOT EXISTS chat_messages (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    sequence_number BIGINT NOT NULL,
    role VARCHAR(32) NOT NULL,
    sender VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'completed',
    agent_id VARCHAR(255),
    agent_name VARCHAR(255),
    error_message TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (session_id, sequence_number)
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_sequence
    ON chat_messages(session_id, sequence_number DESC);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created
    ON chat_messages(session_id, created_at DESC);

CREATE TABLE IF NOT EXISTS chat_message_feedback (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_id VARCHAR(255) NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    agent_id VARCHAR(255),
    feedback_type VARCHAR(32) NOT NULL,
    rating DOUBLE PRECISION,
    text_feedback TEXT,
    user_id VARCHAR(255),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (message_id)
);

CREATE INDEX IF NOT EXISTS idx_chat_feedback_session
    ON chat_message_feedback(session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_feedback_agent
    ON chat_message_feedback(agent_id, created_at DESC);
