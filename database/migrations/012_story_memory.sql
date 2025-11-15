-- Story Memory System Tables
-- For tracking narrative continuity, player decisions, and drift detection

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Story players metadata
CREATE TABLE IF NOT EXISTS story_players (
    player_id UUID PRIMARY KEY REFERENCES players(id) ON DELETE CASCADE,
    broker_book_state JSONB NOT NULL DEFAULT '{}'::jsonb, -- Pages unlocked, rituals known, personality traits
    debt_of_flesh_state JSONB NOT NULL DEFAULT '{}'::jsonb, -- Deaths, Soul-Echo encounters, Corpse-Tender interactions
    surgeon_butcher_score FLOAT NOT NULL DEFAULT 0.0 CHECK (surgeon_butcher_score BETWEEN -1.0 AND 1.0), -- -1.0 = Full Surgeon, 1.0 = Full Butcher
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Arc progress tracking
CREATE TABLE IF NOT EXISTS story_arc_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    arc_id VARCHAR(100) NOT NULL, -- e.g., 'dark.carrion_kin', 'light.crime_empire'
    arc_role VARCHAR(20) NOT NULL CHECK (arc_role IN ('main_arc', 'side_arc', 'experience', 'ambient')),
    progress_state VARCHAR(20) NOT NULL CHECK (progress_state IN ('not_started', 'early', 'mid', 'late', 'completed')),
    last_beat_id VARCHAR(100),
    last_update_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (player_id, arc_id)
);

-- Key decisions log
CREATE TABLE IF NOT EXISTS story_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    session_id UUID,
    decision_id VARCHAR(100) NOT NULL,
    arc_id VARCHAR(100),
    npc_id VARCHAR(100),
    choice_label VARCHAR(200) NOT NULL,
    outcome_tags JSONB NOT NULL DEFAULT '[]'::jsonb, -- ['mercy', 'loyalty', etc.]
    moral_weight FLOAT DEFAULT 0.0, -- Impact on surgeon/butcher score
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_story_decisions_player (player_id),
    INDEX idx_story_decisions_arc (arc_id)
);

-- NPC and faction relationships
CREATE TABLE IF NOT EXISTS story_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    entity_id VARCHAR(100) NOT NULL, -- NPC ID or faction ID
    entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('npc', 'faction')),
    relationship_score FLOAT NOT NULL DEFAULT 0.0 CHECK (relationship_score BETWEEN -100.0 AND 100.0),
    flags JSONB NOT NULL DEFAULT '[]'::jsonb, -- ['trusted', 'betrayed', 'oath_broken', etc.]
    last_interaction VARCHAR(200),
    last_interaction_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (player_id, entity_id)
);

-- Experiences tracking (major life events)
CREATE TABLE IF NOT EXISTS story_experiences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    experience_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'completed', 'failed', 'abandoned')),
    emotional_impact JSONB NOT NULL DEFAULT '{}'::jsonb, -- Category scores for emotional resonance
    cross_references JSONB NOT NULL DEFAULT '[]'::jsonb, -- Links to other experiences
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    INDEX idx_story_experiences_player (player_id),
    INDEX idx_story_experiences_status (status)
);

-- Story memory events (for event sourcing)
CREATE TABLE IF NOT EXISTS story_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    session_id UUID,
    event_type VARCHAR(50) NOT NULL, -- 'arc_beat_reached', 'quest_completed', etc.
    event_data JSONB NOT NULL,
    sequence_num BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_story_events_player (player_id),
    INDEX idx_story_events_type (event_type),
    INDEX idx_story_events_sequence (player_id, sequence_num),
    UNIQUE (player_id, sequence_num) -- Prevent duplicate sequence numbers per player
);

-- Drift detection alerts
CREATE TABLE IF NOT EXISTS story_drift_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID REFERENCES players(id) ON DELETE SET NULL,
    session_id UUID,
    drift_type VARCHAR(50) NOT NULL, -- 'time_allocation', 'quest_allocation', 'theme_consistency'
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('minor', 'moderate', 'major')),
    drift_score FLOAT NOT NULL CHECK (drift_score BETWEEN 0.0 AND 1.0),
    metrics JSONB NOT NULL, -- Detailed metrics that triggered the alert
    recommended_correction TEXT,
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE,
    corrective_action TEXT,
    INDEX idx_drift_alerts_player (player_id),
    INDEX idx_drift_alerts_severity (severity),
    INDEX idx_drift_alerts_detected (detected_at DESC)
);

-- Story conflict alerts
CREATE TABLE IF NOT EXISTS story_conflicts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID REFERENCES players(id) ON DELETE SET NULL,
    session_id UUID,
    conflict_type VARCHAR(50) NOT NULL, -- 'npc_state', 'quest_logic', 'world_state'
    involved_entities JSONB NOT NULL, -- IDs of NPCs, quests, locations involved
    conflicting_facts JSONB NOT NULL, -- What's in conflict
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    INDEX idx_conflicts_player (player_id),
    INDEX idx_conflicts_type (conflict_type),
    INDEX idx_conflicts_resolved (resolved)
);

-- Dark World family standings
CREATE TABLE IF NOT EXISTS dark_world_standings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    family_name VARCHAR(50) NOT NULL CHECK (family_name IN (
        'carrion_kin', 'chatter_swarm', 'stitch_guild', 'moon_clans',
        'vampiric_houses', 'obsidian_synod', 'silent_court', 'leviathan_conclave'
    )),
    standing_score FLOAT NOT NULL DEFAULT 0.0 CHECK (standing_score BETWEEN -100.0 AND 100.0),
    favors_owed INTEGER NOT NULL DEFAULT 0,
    debts_owed INTEGER NOT NULL DEFAULT 0,
    betrayal_count INTEGER NOT NULL DEFAULT 0,
    special_status JSONB NOT NULL DEFAULT '[]'::jsonb, -- ['trusted_supplier', 'marked_enemy', etc.]
    last_interaction TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (player_id, family_name)
);

-- Indexes for performance
CREATE INDEX idx_arc_progress_updated ON story_arc_progress(last_update_at DESC);
CREATE INDEX idx_relationships_updated ON story_relationships(updated_at DESC);
CREATE INDEX idx_experiences_started ON story_experiences(started_at DESC);
CREATE INDEX idx_dark_world_interaction ON dark_world_standings(last_interaction DESC);

-- Triggers to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_story_players_updated_at BEFORE UPDATE ON story_players
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_story_relationships_updated_at BEFORE UPDATE ON story_relationships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dark_world_standings_updated_at BEFORE UPDATE ON dark_world_standings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
