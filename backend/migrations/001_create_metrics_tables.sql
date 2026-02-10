-- Migration: 001_create_metrics_tables.sql
-- Description: Create core metrics infrastructure tables for real-time agent tracking
-- Author: System
-- Date: 2026-02-08

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- 1. Agent Executions Table
-- ============================================================================
-- Tracks every task execution by every agent with complete lifecycle data

CREATE TABLE IF NOT EXISTS agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Agent identification
    agent_id VARCHAR(50) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    
    -- Task identification
    task_id VARCHAR(100) NOT NULL,
    task_type VARCHAR(50),
    
    -- Timing information
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    response_time_ms INTEGER,
    
    -- Execution outcome
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'success', 'failed', 'timeout')),
    success BOOLEAN,
    error_type VARCHAR(50),
    error_message TEXT,
    
    -- Execution data (JSONB for flexible schema)
    input_data JSONB,
    output_data JSONB,
    metadata JSONB,
    
    -- Audit timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX idx_executions_agent_time ON agent_executions(agent_id, started_at DESC);
CREATE INDEX idx_executions_status ON agent_executions(status, started_at DESC);
CREATE INDEX idx_executions_task_type ON agent_executions(task_type, started_at DESC);
CREATE INDEX idx_executions_task_id ON agent_executions(task_id);

-- Add comments for documentation
COMMENT ON TABLE agent_executions IS 'Raw execution records for all agent tasks';
COMMENT ON COLUMN agent_executions.response_time_ms IS 'Time from start to completion in milliseconds';
COMMENT ON COLUMN agent_executions.metadata IS 'Additional contextual information about the execution';

-- ============================================================================
-- 2. Agent Metrics Snapshots Table
-- ============================================================================
-- Pre-aggregated metrics for fast dashboard queries and historical analysis

CREATE TABLE IF NOT EXISTS agent_metrics_snapshots (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    snapshot_time TIMESTAMP NOT NULL,
    
    -- Task completion metrics
    total_tasks INTEGER DEFAULT 0 CHECK (total_tasks >= 0),
    successful_tasks INTEGER DEFAULT 0 CHECK (successful_tasks >= 0),
    failed_tasks INTEGER DEFAULT 0 CHECK (failed_tasks >= 0),
    success_rate DECIMAL(5,2) CHECK (success_rate BETWEEN 0 AND 100),
    
    -- Performance metrics (response time)
    avg_response_time_ms INTEGER CHECK (avg_response_time_ms >= 0),
    p50_response_time_ms INTEGER CHECK (p50_response_time_ms >= 0),
    p95_response_time_ms INTEGER CHECK (p95_response_time_ms >= 0),
    p99_response_time_ms INTEGER CHECK (p99_response_time_ms >= 0),
    
    -- Advanced AI metrics
    elo_rating INTEGER DEFAULT 1500 CHECK (elo_rating BETWEEN 0 AND 3000),
    dream_cycles_completed INTEGER DEFAULT 0 CHECK (dream_cycles_completed >= 0),
    insights_generated INTEGER DEFAULT 0 CHECK (insights_generated >= 0),
    knowledge_nodes_created INTEGER DEFAULT 0 CHECK (knowledge_nodes_created >= 0),
    
    -- Tournament performance
    matches_won INTEGER DEFAULT 0 CHECK (matches_won >= 0),
    matches_lost INTEGER DEFAULT 0 CHECK (matches_lost >= 0),
    matches_drawn INTEGER DEFAULT 0 CHECK (matches_drawn >= 0),
    
    -- Ensure one snapshot per agent per time period
    UNIQUE(agent_id, snapshot_time)
);

-- Indexes for time-series queries
CREATE INDEX idx_snapshots_agent_time ON agent_metrics_snapshots(agent_id, snapshot_time DESC);
CREATE INDEX idx_snapshots_time ON agent_metrics_snapshots(snapshot_time DESC);

COMMENT ON TABLE agent_metrics_snapshots IS 'Periodic snapshots of aggregated metrics for each agent';
COMMENT ON COLUMN agent_metrics_snapshots.elo_rating IS 'Tournament ELO rating (default 1500)';

-- ============================================================================
-- 3. Tournament Matches Table
-- ============================================================================
-- Records GAIA tournament matches for ELO calculation and leaderboard

CREATE TABLE IF NOT EXISTS tournament_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Tournament context
    tournament_id VARCHAR(100),
    round_number INTEGER CHECK (round_number > 0),
    
    -- Participants
    agent1_id VARCHAR(50) NOT NULL,
    agent2_id VARCHAR(50) NOT NULL,
    agent1_elo_before INTEGER CHECK (agent1_elo_before BETWEEN 0 AND 3000),
    agent2_elo_before INTEGER CHECK (agent2_elo_before BETWEEN 0 AND 3000),
    
    -- Match outcome
    winner_id VARCHAR(50),
    loser_id VARCHAR(50),
    is_draw BOOLEAN DEFAULT FALSE,
    score_agent1 DECIMAL(10,2),
    score_agent2 DECIMAL(10,2),
    
    -- ELO rating updates
    agent1_elo_after INTEGER CHECK (agent1_elo_after BETWEEN 0 AND 3000),
    agent2_elo_after INTEGER CHECK (agent2_elo_after BETWEEN 0 AND 3000),
    elo_change INTEGER,
    
    -- Timing
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    
    -- Additional context
    match_type VARCHAR(50),
    metadata JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Validate participants are different
    CHECK (agent1_id != agent2_id),
    
    -- Validate winner/loser consistency
    CHECK (
        (is_draw = TRUE AND winner_id IS NULL AND loser_id IS NULL) OR
        (is_draw = FALSE AND winner_id IS NOT NULL AND loser_id IS NOT NULL) OR
        (winner_id IS NULL AND loser_id IS NULL)
    )
);

-- Indexes for match history and leaderboard queries
CREATE INDEX idx_matches_agents ON tournament_matches(agent1_id, agent2_id, created_at DESC);
CREATE INDEX idx_matches_tournament ON tournament_matches(tournament_id, round_number);
CREATE INDEX idx_matches_agent1 ON tournament_matches(agent1_id, created_at DESC);
CREATE INDEX idx_matches_agent2 ON tournament_matches(agent2_id, created_at DESC);
CREATE INDEX idx_matches_winner ON tournament_matches(winner_id) WHERE winner_id IS NOT NULL;

COMMENT ON TABLE tournament_matches IS 'Records of all GAIA tournament matches for ELO tracking';
COMMENT ON COLUMN tournament_matches.elo_change IS 'Rating points gained/lost by winner';

-- ============================================================================
-- 4. Dream Cycles Table
-- ============================================================================
-- Tracks Oneiroi dream system activity and insights

CREATE TABLE IF NOT EXISTS dream_cycles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(50) NOT NULL,
    
    -- Dream classification
    dream_type VARCHAR(50) CHECK (dream_type IN ('exploration', 'consolidation', 'innovation', 'reflection')),
    cycle_number INTEGER CHECK (cycle_number > 0),
    
    -- Timing information
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_ms INTEGER CHECK (duration_ms >= 0),
    
    -- Dream outcomes
    insights_generated INTEGER DEFAULT 0 CHECK (insights_generated >= 0),
    patterns_discovered INTEGER DEFAULT 0 CHECK (patterns_discovered >= 0),
    knowledge_consolidated BOOLEAN DEFAULT FALSE,
    
    -- Quality metrics (0.0 to 1.0 scale)
    coherence_score DECIMAL(5,2) CHECK (coherence_score BETWEEN 0 AND 1),
    novelty_score DECIMAL(5,2) CHECK (novelty_score BETWEEN 0 AND 1),
    utility_score DECIMAL(5,2) CHECK (utility_score BETWEEN 0 AND 1),
    
    -- Dream content
    dream_narrative TEXT,
    insights JSONB,
    metadata JSONB,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for dream analysis
CREATE INDEX idx_dreams_agent_time ON dream_cycles(agent_id, started_at DESC);
CREATE INDEX idx_dreams_type ON dream_cycles(dream_type, started_at DESC);
CREATE INDEX idx_dreams_quality ON dream_cycles(coherence_score DESC, novelty_score DESC, utility_score DESC);

COMMENT ON TABLE dream_cycles IS 'Oneiroi dream system activity and insight generation';
COMMENT ON COLUMN dream_cycles.coherence_score IS 'How logically consistent the dream was (0-1)';
COMMENT ON COLUMN dream_cycles.novelty_score IS 'How novel the discovered patterns were (0-1)';
COMMENT ON COLUMN dream_cycles.utility_score IS 'How useful the insights were (0-1)';

-- ============================================================================
-- 5. Helper Functions
-- ============================================================================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for agent_executions table
CREATE TRIGGER update_agent_executions_updated_at
    BEFORE UPDATE ON agent_executions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 6. Initial Data
-- ============================================================================

-- Insert initial snapshot records for known agents (all start at ELO 1500)
INSERT INTO agent_metrics_snapshots (agent_id, snapshot_time, elo_rating, total_tasks, successful_tasks, failed_tasks, success_rate)
VALUES 
    ('data-analyst', NOW(), 1500, 0, 0, 0, 0.0),
    ('designer', NOW(), 1500, 0, 0, 0, 0.0),
    ('financial', NOW(), 1500, 0, 0, 0, 0.0),
    ('translator', NOW(), 1500, 0, 0, 0, 0.0)
ON CONFLICT (agent_id, snapshot_time) DO NOTHING;

-- ============================================================================
-- Migration Complete
-- ============================================================================
