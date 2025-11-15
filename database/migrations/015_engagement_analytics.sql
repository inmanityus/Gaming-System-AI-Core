-- Engagement & Addiction Analytics Tables
-- For tracking emotional engagement and cohort-level addiction risks

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Engagement events table (R-EMO-DATA-001, R-EMO-DATA-002, R-EMO-DATA-003)
CREATE TABLE IF NOT EXISTS engagement_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL,
    player_id UUID,  -- Optional, pseudonymized
    actor_type VARCHAR(20) NOT NULL CHECK (actor_type IN ('real_player', 'ai_player')),
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('npc_interaction', 'moral_choice', 'session_metrics', 'ai_run')),
    
    -- Common fields
    timestamp TIMESTAMP NOT NULL,
    build_id VARCHAR(128) NOT NULL,
    environment VARCHAR(50),  -- e.g., 'dev', 'staging', 'prod'
    
    -- NPC interaction fields
    npc_id VARCHAR(128),
    interaction_type VARCHAR(50) CHECK (interaction_type IN ('dialogue', 'gift', 'assist', 'harm', 'ignore')),
    choice_id VARCHAR(128),
    choice_label TEXT,
    help_harm_flag VARCHAR(20) CHECK (help_harm_flag IN ('helpful', 'harmful', 'neutral')),
    location_id VARCHAR(128),
    arc_id VARCHAR(128),
    experience_id VARCHAR(128),
    
    -- Moral choice fields
    scene_id VARCHAR(128),
    options JSONB,  -- Array of {option_id, option_label, tags[]}
    selected_option_id VARCHAR(128),
    decision_latency_ms INTEGER,
    num_retries INTEGER DEFAULT 0,
    reloaded_save BOOLEAN DEFAULT FALSE,
    
    -- Session metrics fields
    session_start TIMESTAMP,
    session_end TIMESTAMP,
    total_duration_minutes INTEGER,
    time_of_day_bucket VARCHAR(20) CHECK (time_of_day_bucket IN ('early_morning', 'morning', 'afternoon', 'evening', 'late_night')),
    day_of_week INTEGER CHECK (day_of_week >= 0 AND day_of_week <= 6),  -- 0=Sunday
    num_sessions_last_7_days INTEGER,
    num_sessions_last_24_hours INTEGER,
    is_return_session BOOLEAN DEFAULT FALSE,
    time_since_last_session_seconds INTEGER,
    platform VARCHAR(50),
    region VARCHAR(50),
    
    -- AI run fields
    ai_run_id VARCHAR(128),
    personality_profile VARCHAR(50),
    total_npcs_interacted INTEGER,
    moral_choices_made INTEGER,
    help_harm_ratio FLOAT,
    exploration_coverage FLOAT CHECK (exploration_coverage >= 0 AND exploration_coverage <= 1),
    run_start TIMESTAMP,
    run_end TIMESTAMP,
    total_duration_hours INTEGER,
    scenario_id VARCHAR(128),
    
    -- Additional context (flexible)
    additional_context JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Indexes for analytics
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_engagement_session (session_id),
    INDEX idx_engagement_player (player_id),
    INDEX idx_engagement_event_type (event_type),
    INDEX idx_engagement_timestamp (timestamp),
    INDEX idx_engagement_build (build_id),
    INDEX idx_engagement_npc (npc_id),
    INDEX idx_engagement_arc (arc_id)
);

-- Engagement aggregates table for computed metrics
CREATE TABLE IF NOT EXISTS engagement_aggregates (
    aggregate_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    aggregate_type VARCHAR(50) NOT NULL CHECK (aggregate_type IN ('npc_attachment', 'moral_tension', 'engagement_profile')),
    
    -- Aggregation keys
    cohort_id VARCHAR(128),  -- e.g., "NA-18-25-PC"
    npc_id VARCHAR(128),
    arc_id VARCHAR(128),
    scene_id VARCHAR(128),
    experience_id VARCHAR(128),
    
    -- Time window
    build_id VARCHAR(128) NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    
    -- NPC attachment metrics (R-EMO-MET-001)
    protection_harm_ratio FLOAT,
    attention_score FLOAT CHECK (attention_score >= 0 AND attention_score <= 1),
    abandonment_frequency FLOAT CHECK (abandonment_frequency >= 0 AND abandonment_frequency <= 1),
    total_interactions INTEGER,
    helpful_actions INTEGER,
    harmful_actions INTEGER,
    neutral_actions INTEGER,
    total_proximity_time_seconds INTEGER,
    
    -- Moral tension metrics (R-EMO-MET-002)
    tension_index FLOAT CHECK (tension_index >= 0 AND tension_index <= 1),
    choice_distribution_entropy FLOAT,
    avg_decision_latency_seconds FLOAT,
    total_choices INTEGER,
    reload_count INTEGER,
    option_counts JSONB,  -- {option_id: count}
    
    -- Engagement profile (R-EMO-MET-003)
    profile_id VARCHAR(128),
    profile_name VARCHAR(128),  -- e.g., "lore-driven explorer"
    profile_confidence FLOAT CHECK (profile_confidence >= 0 AND profile_confidence <= 1),
    characteristic_behaviors TEXT[],
    
    -- Metadata
    computed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,  -- Additional computed metrics
    
    UNIQUE(aggregate_type, cohort_id, npc_id, arc_id, scene_id, build_id, period_start),
    INDEX idx_engagement_agg_type (aggregate_type),
    INDEX idx_engagement_agg_cohort (cohort_id),
    INDEX idx_engagement_agg_build (build_id)
);

-- Addiction risk reports table (R-EMO-ADD-001, R-EMO-ADD-003)
CREATE TABLE IF NOT EXISTS addiction_risk_reports (
    report_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Cohort identification (NO player IDs)
    cohort_id VARCHAR(128) NOT NULL,
    region VARCHAR(50),
    age_band VARCHAR(20),  -- e.g., "18-25", "26-35"
    platform VARCHAR(50),
    cohort_size INTEGER NOT NULL,
    
    -- Report period
    report_period VARCHAR(50) NOT NULL,  -- e.g., "2025-11-14/P7D"
    
    -- Risk indicators
    avg_daily_session_hours FLOAT,
    night_time_play_fraction FLOAT CHECK (night_time_play_fraction >= 0 AND night_time_play_fraction <= 1),
    rapid_session_return_rate FLOAT CHECK (rapid_session_return_rate >= 0 AND rapid_session_return_rate <= 1),
    weekend_spike_ratio FLOAT,
    
    -- Pattern detection
    high_risk_patterns TEXT[],  -- e.g., ["3am_regular", "12hr_binge"]
    associated_systems TEXT[],  -- Game systems correlated with risk
    
    -- Risk assessment
    overall_risk_level VARCHAR(20) NOT NULL CHECK (overall_risk_level IN ('low', 'medium', 'high', 'critical')),
    risk_summary TEXT,
    recommendations TEXT[],
    
    -- Metadata
    computed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confidence_percentage INTEGER CHECK (confidence_percentage >= 0 AND confidence_percentage <= 100),
    build_id VARCHAR(128) NOT NULL,
    notes TEXT,
    
    INDEX idx_addiction_risk_cohort (cohort_id),
    INDEX idx_addiction_risk_level (overall_risk_level),
    INDEX idx_addiction_risk_computed (computed_at)
);

-- Engagement profile definitions (reference data)
CREATE TABLE IF NOT EXISTS engagement_profile_definitions (
    profile_id VARCHAR(128) PRIMARY KEY,
    profile_name VARCHAR(128) NOT NULL UNIQUE,
    profile_description TEXT,
    
    -- Behavioral criteria
    criteria JSONB NOT NULL,  -- Rules for classifying into this profile
    example_behaviors TEXT[],
    typical_metrics JSONB,
    
    -- Status
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert default engagement profiles
INSERT INTO engagement_profile_definitions (profile_id, profile_name, profile_description, criteria, example_behaviors) VALUES
    ('prof-001', 'lore-driven explorer', 'Players who prioritize story and world exploration', 
     '{"min_dialogue_completion": 0.8, "exploration_coverage": 0.7}',
     ARRAY['reads all books', 'exhausts dialogue trees', 'explores hidden areas']),
    
    ('prof-002', 'combat-focused', 'Players who prioritize combat and action', 
     '{"combat_participation": 0.9, "dialogue_skip_rate": 0.6}',
     ARRAY['skips dialogue', 'seeks combat encounters', 'optimizes loadouts']),
    
    ('prof-003', 'completionist', 'Players who aim to complete everything', 
     '{"quest_completion": 0.95, "collectible_rate": 0.9}',
     ARRAY['completes all quests', 'collects all items', 'unlocks all achievements']),
    
    ('prof-004', 'moral extremist', 'Players who consistently choose extreme moral options', 
     '{"extreme_choice_rate": 0.8, "moral_consistency": 0.9}',
     ARRAY['always evil/good choices', 'no middle ground', 'strong role-play']),
    
    ('prof-005', 'social butterfly', 'Players who maximize NPC interactions', 
     '{"npc_interaction_rate": 0.9, "gift_giving_rate": 0.7}',
     ARRAY['talks to everyone', 'gives many gifts', 'builds relationships'])
ON CONFLICT (profile_id) DO NOTHING;

-- Session cohort mapping (for privacy-preserving analytics)
CREATE TABLE IF NOT EXISTS session_cohorts (
    session_id UUID PRIMARY KEY,
    cohort_id VARCHAR(128) NOT NULL,
    
    -- Cohort components (no PII)
    region VARCHAR(50),
    age_band VARCHAR(20),
    platform VARCHAR(50),
    
    -- Assignment metadata
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_session_cohort (cohort_id)
);

-- Indexes for performance
CREATE INDEX idx_engagement_events_composite ON engagement_events(event_type, timestamp, build_id);
CREATE INDEX idx_engagement_events_session_type ON engagement_events(session_id, event_type);
CREATE INDEX idx_engagement_aggregates_period ON engagement_aggregates(period_start, period_end);

-- Data retention and privacy comments
COMMENT ON TABLE engagement_events IS 'Raw telemetry events with pseudonymized player IDs. Subject to retention policies per R-SYS-DATA-003.';
COMMENT ON TABLE addiction_risk_reports IS 'Cohort-level addiction risk indicators. MUST NOT contain individual player data per R-EMO-ADD-002.';
COMMENT ON COLUMN engagement_events.player_id IS 'Pseudonymized player ID, optional. Never store real identities.';
COMMENT ON COLUMN addiction_risk_reports.cohort_id IS 'Aggregate cohort identifier only. No individual player tracking allowed.';
