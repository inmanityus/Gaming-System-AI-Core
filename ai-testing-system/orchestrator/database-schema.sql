-- Body Broker QA System Database Schema
-- AI-Driven Game Testing System (Tier 3)
-- Database: bodybroker_qa on gaming-system-bodybroker-db

CREATE SCHEMA IF NOT EXISTS qa;

-- Test runs table
CREATE TABLE IF NOT EXISTS qa.test_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    git_commit VARCHAR(40) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL, -- 'running', 'completed', 'failed'
    test_filter VARCHAR(255),
    total_tests INTEGER,
    passed_tests INTEGER,
    failed_tests INTEGER,
    duration_seconds FLOAT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Captures table
CREATE TABLE IF NOT EXISTS qa.captures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    capture_id VARCHAR(255) UNIQUE NOT NULL,
    test_run_id UUID REFERENCES qa.test_runs(id),
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    screenshot_s3_key TEXT NOT NULL,
    telemetry_s3_key TEXT NOT NULL,
    s3_bucket VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'pending_analysis', 'analyzing', 'complete', 'failed'
    perceptual_hash VARCHAR(64),
    cache_hit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    INDEX idx_captures_status (status),
    INDEX idx_captures_event_type (event_type),
    INDEX idx_captures_perceptual_hash (perceptual_hash)
);

-- Analysis results table (from vision models)
CREATE TABLE IF NOT EXISTS qa.analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    capture_id UUID REFERENCES qa.captures(id) NOT NULL,
    model_name VARCHAR(50) NOT NULL, -- 'gemini-2.5-pro', 'gpt-4o', 'claude-sonnet-4.5'
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    is_issue BOOLEAN NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'atmosphere', 'ux', 'visual_bug', 'performance'
    description TEXT NOT NULL,
    recommendations JSONB,
    raw_response JSONB,
    analysis_duration_seconds FLOAT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    INDEX idx_analysis_capture (capture_id),
    INDEX idx_analysis_model (model_name)
);

-- Consensus results table
CREATE TABLE IF NOT EXISTS qa.consensus_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    capture_id UUID REFERENCES qa.captures(id) UNIQUE NOT NULL,
    issue_flagged BOOLEAN NOT NULL,
    consensus_models TEXT[], -- Array of model names that agreed
    average_confidence FLOAT NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    recommendations JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    INDEX idx_consensus_flagged (issue_flagged),
    INDEX idx_consensus_category (category)
);

-- Structured recommendations table
CREATE TABLE IF NOT EXISTS qa.structured_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id VARCHAR(50) UNIQUE NOT NULL,
    capture_id UUID REFERENCES qa.captures(id) NOT NULL,
    consensus_id UUID REFERENCES qa.consensus_results(id) NOT NULL,
    confidence FLOAT NOT NULL,
    severity VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    git_commit VARCHAR(40) NOT NULL,
    test_case VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    analysis TEXT NOT NULL,
    screenshot_path TEXT NOT NULL,
    telemetry_path TEXT NOT NULL,
    models_consensus JSONB NOT NULL,
    recommendation JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'accepted', 'rejected', 'in_progress', 'resolved'
    jira_ticket_id VARCHAR(50),
    reviewer_notes TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    INDEX idx_recommendations_status (status),
    INDEX idx_recommendations_severity (severity),
    INDEX idx_recommendations_category (category)
);

-- Human feedback table (for model improvement)
CREATE TABLE IF NOT EXISTS qa.human_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_id UUID REFERENCES qa.structured_recommendations(id) NOT NULL,
    action VARCHAR(20) NOT NULL, -- 'accepted', 'rejected', 'edited'
    feedback_text TEXT,
    model_accuracy_rating INTEGER CHECK (model_accuracy_rating BETWEEN 1 AND 5),
    reviewer VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- System statistics table
CREATE TABLE IF NOT EXISTS qa.system_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stat_date DATE NOT NULL UNIQUE,
    total_captures INTEGER DEFAULT 0,
    total_analyses INTEGER DEFAULT 0,
    issues_flagged INTEGER DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    cache_misses INTEGER DEFAULT 0,
    vision_api_calls INTEGER DEFAULT 0,
    estimated_cost_usd NUMERIC(10,2),
    estimated_savings_usd NUMERIC(10,2),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_test_runs_started ON qa.test_runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_captures_created ON qa.captures(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_recommendations_created ON qa.structured_recommendations(created_at DESC);

-- Grant permissions (adjust username as needed)
GRANT ALL ON SCHEMA qa TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA qa TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA qa TO postgres;

