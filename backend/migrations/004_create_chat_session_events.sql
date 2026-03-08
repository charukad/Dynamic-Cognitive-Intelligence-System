CREATE TABLE IF NOT EXISTS chat_session_events (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    room_id VARCHAR(64),
    room_title VARCHAR(255),
    description TEXT NOT NULL,
    severity VARCHAR(32) NOT NULL DEFAULT 'info',
    related_message_id VARCHAR(255) REFERENCES chat_messages(id) ON DELETE SET NULL,
    related_agent_id VARCHAR(255),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_session_events_session_created
    ON chat_session_events(session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_session_events_session_room
    ON chat_session_events(session_id, room_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_session_events_session_type
    ON chat_session_events(session_id, event_type, created_at DESC);
