-- The Body Broker - Initial Database Schema
-- Migration: 001_initial_schema
-- Created: 2025-01-29
-- Description: Creates all core tables, indexes, constraints, and relationships

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector extension for personality vector similarity search (if available)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- PLAYERS TABLE
-- ============================================================================
CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    steam_id VARCHAR(64) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL,
    tier VARCHAR(20) NOT NULL DEFAULT 'free', -- free/premium/whale
    stats JSONB NOT NULL DEFAULT '{}',
    inventory JSONB NOT NULL DEFAULT '[]',
    money NUMERIC(12, 2) NOT NULL DEFAULT 0.0,
    reputation INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    xp NUMERIC(12, 2) NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for players
CREATE INDEX idx_players_steam_id ON players(steam_id);
CREATE INDEX idx_players_tier ON players(tier);
CREATE INDEX idx_players_level ON players(level);
CREATE INDEX idx_players_stats ON players USING GIN(stats);
CREATE INDEX idx_players_inventory ON players USING GIN(inventory);

-- ============================================================================
-- GAME STATES TABLE
-- ============================================================================
CREATE TABLE game_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL,
    current_world VARCHAR(20) NOT NULL DEFAULT 'day',
    location VARCHAR(100),
    position JSONB,
    active_quests JSONB NOT NULL DEFAULT '[]',
    session_data JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_game_states_player FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

-- Indexes for game_states
CREATE INDEX idx_game_states_player_id ON game_states(player_id);
CREATE INDEX idx_game_states_is_active ON game_states(is_active);
CREATE INDEX idx_game_states_current_world ON game_states(current_world);
CREATE INDEX idx_game_states_active_quests ON game_states USING GIN(active_quests);
CREATE INDEX idx_game_states_session_data ON game_states USING GIN(session_data);

-- ============================================================================
-- STORY NODES TABLE
-- ============================================================================
CREATE TABLE story_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL,
    node_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    narrative_content TEXT,
    choices JSONB NOT NULL DEFAULT '[]',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    prerequisites JSONB NOT NULL DEFAULT '[]',
    consequences JSONB NOT NULL DEFAULT '{}',
    meta_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_story_nodes_player FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

-- Indexes for story_nodes
CREATE INDEX idx_story_nodes_player_id ON story_nodes(player_id);
CREATE INDEX idx_story_nodes_node_type ON story_nodes(node_type);
CREATE INDEX idx_story_nodes_status ON story_nodes(status);
CREATE INDEX idx_story_nodes_choices ON story_nodes USING GIN(choices);
CREATE INDEX idx_story_nodes_prerequisites ON story_nodes USING GIN(prerequisites);
CREATE INDEX idx_story_nodes_consequences ON story_nodes USING GIN(consequences);

-- ============================================================================
-- TRANSACTIONS TABLE
-- ============================================================================
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    stripe_payment_intent_id VARCHAR(255) UNIQUE,
    amount NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    description VARCHAR(500),
    meta_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_transactions_player FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

-- Indexes for transactions
CREATE INDEX idx_transactions_player_id ON transactions(player_id);
CREATE INDEX idx_transactions_stripe_payment_intent_id ON transactions(stripe_payment_intent_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_transaction_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);
CREATE INDEX idx_transactions_metadata ON transactions USING GIN(meta_data);

-- ============================================================================
-- WORLD STATES TABLE
-- ============================================================================
CREATE TABLE world_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    world_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    day_phase VARCHAR(20) NOT NULL DEFAULT 'day',
    weather VARCHAR(50),
    faction_power JSONB NOT NULL DEFAULT '{}',
    global_events JSONB NOT NULL DEFAULT '[]',
    economic_state JSONB NOT NULL DEFAULT '{}',
    npc_population JSONB NOT NULL DEFAULT '{}',
    territory_control JSONB NOT NULL DEFAULT '{}',
    simulation_data JSONB NOT NULL DEFAULT '{}',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for world_states
CREATE INDEX idx_world_states_world_time ON world_states(world_time);
CREATE INDEX idx_world_states_day_phase ON world_states(day_phase);
CREATE INDEX idx_world_states_faction_power ON world_states USING GIN(faction_power);
CREATE INDEX idx_world_states_global_events ON world_states USING GIN(global_events);
CREATE INDEX idx_world_states_economic_state ON world_states USING GIN(economic_state);
CREATE INDEX idx_world_states_npc_population ON world_states USING GIN(npc_population);
CREATE INDEX idx_world_states_territory_control ON world_states USING GIN(territory_control);

-- ============================================================================
-- FACTIONS TABLE
-- ============================================================================
CREATE TABLE factions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    faction_type VARCHAR(50) NOT NULL,
    description TEXT,
    power_level INTEGER NOT NULL DEFAULT 50,
    territory JSONB NOT NULL DEFAULT '[]',
    relationships JSONB NOT NULL DEFAULT '{}',
    hierarchy JSONB NOT NULL DEFAULT '{}',
    goals JSONB NOT NULL DEFAULT '[]',
    meta_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for factions
CREATE INDEX idx_factions_name ON factions(name);
CREATE INDEX idx_factions_faction_type ON factions(faction_type);
CREATE INDEX idx_factions_power_level ON factions(power_level);
CREATE INDEX idx_factions_territory ON factions USING GIN(territory);
CREATE INDEX idx_factions_relationships ON factions USING GIN(relationships);
CREATE INDEX idx_factions_hierarchy ON factions USING GIN(hierarchy);

-- ============================================================================
-- NPCS TABLE
-- ============================================================================
CREATE TABLE npcs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    world_state_id UUID NOT NULL,
    faction_id UUID,
    name VARCHAR(100) NOT NULL,
    npc_type VARCHAR(50) NOT NULL,
    personality_vector JSONB NOT NULL,
    stats JSONB NOT NULL DEFAULT '{}',
    goal_stack JSONB NOT NULL DEFAULT '[]',
    current_location VARCHAR(100),
    current_state VARCHAR(50) NOT NULL DEFAULT 'idle',
    relationships JSONB NOT NULL DEFAULT '{}',
    episodic_memory_id VARCHAR(255),
    meta_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_npcs_world_state FOREIGN KEY (world_state_id) REFERENCES world_states(id) ON DELETE CASCADE,
    CONSTRAINT fk_npcs_faction FOREIGN KEY (faction_id) REFERENCES factions(id) ON DELETE SET NULL
);

-- Indexes for npcs
CREATE INDEX idx_npcs_world_state_id ON npcs(world_state_id);
CREATE INDEX idx_npcs_faction_id ON npcs(faction_id);
CREATE INDEX idx_npcs_npc_type ON npcs(npc_type);
CREATE INDEX idx_npcs_current_location ON npcs(current_location);
CREATE INDEX idx_npcs_current_state ON npcs(current_state);
CREATE INDEX idx_npcs_personality_vector ON npcs USING GIN(personality_vector);
CREATE INDEX idx_npcs_stats ON npcs USING GIN(stats);
CREATE INDEX idx_npcs_goal_stack ON npcs USING GIN(goal_stack);
CREATE INDEX idx_npcs_relationships ON npcs USING GIN(relationships);

-- ============================================================================
-- AUGMENTATIONS TABLE
-- ============================================================================
CREATE TABLE augmentations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    cost NUMERIC(12, 2) NOT NULL DEFAULT 0.0,
    stats_modifier JSONB NOT NULL DEFAULT '{}',
    requirements JSONB NOT NULL DEFAULT '{}',
    meta_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for augmentations
CREATE INDEX idx_augmentations_name ON augmentations(name);
CREATE INDEX idx_augmentations_category ON augmentations(category);
CREATE INDEX idx_augmentations_cost ON augmentations(cost);
CREATE INDEX idx_augmentations_stats_modifier ON augmentations USING GIN(stats_modifier);
CREATE INDEX idx_augmentations_requirements ON augmentations USING GIN(requirements);

-- ============================================================================
-- PLAYER-AUGMENTATIONS ASSOCIATION TABLE (Many-to-Many)
-- ============================================================================
CREATE TABLE player_augmentations (
    player_id UUID NOT NULL,
    augmentation_id UUID NOT NULL,
    acquired_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, augmentation_id),
    CONSTRAINT fk_player_augmentations_player FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    CONSTRAINT fk_player_augmentations_augmentation FOREIGN KEY (augmentation_id) REFERENCES augmentations(id) ON DELETE CASCADE
);

-- Indexes for player_augmentations
CREATE INDEX idx_player_augmentations_player_id ON player_augmentations(player_id);
CREATE INDEX idx_player_augmentations_augmentation_id ON player_augmentations(augmentation_id);

-- ============================================================================
-- TRIGGERS: Update updated_at timestamps automatically
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_game_states_updated_at BEFORE UPDATE ON game_states
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_story_nodes_updated_at BEFORE UPDATE ON story_nodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_world_states_updated_at BEFORE UPDATE ON world_states
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_factions_updated_at BEFORE UPDATE ON factions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_npcs_updated_at BEFORE UPDATE ON npcs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_augmentations_updated_at BEFORE UPDATE ON augmentations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS: Document tables
-- ============================================================================
COMMENT ON TABLE players IS 'Player accounts with stats, inventory, and progression';
COMMENT ON TABLE game_states IS 'Active game session states for each player';
COMMENT ON TABLE story_nodes IS 'Story progression and narrative nodes for player quests';
COMMENT ON TABLE transactions IS 'Payment and economy transactions (Stripe integration)';
COMMENT ON TABLE world_states IS 'World simulation state for Story Teller service';
COMMENT ON TABLE factions IS 'Faction relationships and power dynamics';
COMMENT ON TABLE npcs IS 'NPC entities with 50-dimensional personality vectors';
COMMENT ON TABLE augmentations IS 'Body modification catalog (supernatural powers, upgrades)';
COMMENT ON TABLE player_augmentations IS 'Many-to-many relationship between players and augmentations';

