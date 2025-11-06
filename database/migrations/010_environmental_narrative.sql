-- Environmental Narrative Service Database Schema
-- Migration: 010_environmental_narrative.sql
-- Date: 2025-01-29

-- Story scenes table
CREATE TABLE IF NOT EXISTS story_scenes (
    scene_id UUID PRIMARY KEY,
    scene_type VARCHAR(50) NOT NULL,
    location_x FLOAT NOT NULL,
    location_y FLOAT NOT NULL,
    location_z FLOAT NOT NULL,
    clutter_density INTEGER NOT NULL,
    objects JSONB NOT NULL,  -- Array of object metadata
    discovery_markers TEXT[],
    generated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Object metadata table
CREATE TABLE IF NOT EXISTS object_metadata (
    object_id UUID PRIMARY KEY,
    object_type VARCHAR(100) NOT NULL,
    narrative_weight INTEGER NOT NULL,  -- 1=LOW, 2=MEDIUM, 3=HIGH, 4=CRITICAL
    story_tags TEXT[],
    wear_state FLOAT DEFAULT 0.0,  -- 0.0 = pristine, 1.0 = destroyed
    damage_state FLOAT DEFAULT 0.0,  -- 0.0 = undamaged, 1.0 = destroyed
    temporal_decay FLOAT DEFAULT 0.0,  -- How much time has passed
    relationship_rules JSONB DEFAULT '[]',
    placement_context JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Environmental history table
CREATE TABLE IF NOT EXISTS environmental_history (
    change_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    change_type VARCHAR(50) NOT NULL,  -- "player_action", "npc_trace", "weather_erosion"
    location_x FLOAT NOT NULL,
    location_y FLOAT NOT NULL,
    location_z FLOAT NOT NULL,
    description TEXT NOT NULL,
    player_id UUID,
    timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Discovery rewards table
CREATE TABLE IF NOT EXISTS discovery_rewards (
    discovery_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL,
    object_id UUID REFERENCES object_metadata(object_id),
    scene_id UUID REFERENCES story_scenes(scene_id),
    reward_type VARCHAR(50) NOT NULL,  -- "narrative", "item", "experience", "lore"
    reward_value FLOAT NOT NULL,
    noticed BOOLEAN NOT NULL DEFAULT FALSE,
    discovered_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_story_scenes_location ON story_scenes(location_x, location_y, location_z);
CREATE INDEX IF NOT EXISTS idx_story_scenes_type ON story_scenes(scene_type);
CREATE INDEX IF NOT EXISTS idx_story_scenes_generated ON story_scenes(generated_at DESC);

CREATE INDEX IF NOT EXISTS idx_object_metadata_type ON object_metadata(object_type);
CREATE INDEX IF NOT EXISTS idx_object_metadata_weight ON object_metadata(narrative_weight);

CREATE INDEX IF NOT EXISTS idx_environmental_history_location ON environmental_history(location_x, location_y, location_z);
CREATE INDEX IF NOT EXISTS idx_environmental_history_time ON environmental_history(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_environmental_history_type ON environmental_history(change_type);
CREATE INDEX IF NOT EXISTS idx_environmental_history_player ON environmental_history(player_id) WHERE player_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_discovery_rewards_player ON discovery_rewards(player_id, discovered_at DESC);
CREATE INDEX IF NOT EXISTS idx_discovery_rewards_object ON discovery_rewards(object_id) WHERE object_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_discovery_rewards_scene ON discovery_rewards(scene_id) WHERE scene_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_discovery_rewards_noticed ON discovery_rewards(noticed, discovered_at DESC);

