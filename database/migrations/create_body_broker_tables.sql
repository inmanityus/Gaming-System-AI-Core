-- Body Broker Database Tables
-- Migrates the game to support all Body Broker mechanics

-- Body parts inventory
CREATE TABLE IF NOT EXISTS body_parts (
    part_id VARCHAR(255) PRIMARY KEY,
    part_type VARCHAR(50) NOT NULL,
    quality VARCHAR(20) NOT NULL,
    base_value DECIMAL(10,2) NOT NULL,
    actual_value DECIMAL(10,2) NOT NULL,
    harvested_at TIMESTAMP NOT NULL,
    decay_time_hours DECIMAL(5,2) DEFAULT 24.0,
    target_id VARCHAR(255),
    extraction_method VARCHAR(50),
    tool_quality VARCHAR(20),
    player_skill DECIMAL(3,2),
    is_sold BOOLEAN DEFAULT FALSE,
    sold_to VARCHAR(255),
    sold_at TIMESTAMP,
    metadata JSONB
);

-- Client relationships
CREATE TABLE IF NOT EXISTS dark_clients (
    client_id VARCHAR(255) PRIMARY KEY,
    client_name VARCHAR(255) NOT NULL,
    family VARCHAR(50) NOT NULL,
    species VARCHAR(100),
    tier VARCHAR(20) NOT NULL,
    reputation INT DEFAULT 0,
    satisfaction_level INT DEFAULT 50,
    transaction_count INT DEFAULT 0,
    first_contact TIMESTAMP,
    last_contact TIMESTAMP,
    is_unlocked BOOLEAN DEFAULT FALSE,
    preferences JSONB,
    secrets_unlocked INT DEFAULT 0
);

-- Transaction history
CREATE TABLE IF NOT EXISTS broker_transactions (
    transaction_id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) REFERENCES dark_clients(client_id),
    part_ids TEXT[],
    negotiation_outcome VARCHAR(20),
    base_price DECIMAL(10,2),
    final_price DECIMAL(10,2),
    payment_drug_type VARCHAR(50),
    payment_quantity DECIMAL(10,2),
    reputation_change INT,
    transaction_date TIMESTAMP DEFAULT NOW(),
    player_tactics TEXT[],
    success BOOLEAN
);

-- Morality tracking
CREATE TABLE IF NOT EXISTS player_morality (
    player_id VARCHAR(255) PRIMARY KEY,
    moral_path VARCHAR(20) DEFAULT 'mixed',
    innocents_killed INT DEFAULT 0,
    deserving_killed INT DEFAULT 0,
    neutral_killed INT DEFAULT 0,
    total_kills INT DEFAULT 0,
    vigilante_respect INT DEFAULT 0,
    surgeon_supply_penalty DECIMAL(3,2) DEFAULT 0.0,
    dark_efficiency_rating INT DEFAULT 50,
    human_notoriety INT DEFAULT 0,
    butcher_heat_level INT DEFAULT 0,
    fae_amusement_level INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Kill records
CREATE TABLE IF NOT EXISTS kill_records (
    kill_id SERIAL PRIMARY KEY,
    player_id VARCHAR(255),
    target_id VARCHAR(255) NOT NULL,
    target_type VARCHAR(20) NOT NULL,
    kill_timestamp TIMESTAMP DEFAULT NOW(),
    justification TEXT,
    witnesses INT DEFAULT 0,
    collateral_damage BOOLEAN DEFAULT FALSE,
    parts_harvested TEXT[]
);

-- Drug inventory
CREATE TABLE IF NOT EXISTS drug_inventory (
    drug_id VARCHAR(255) PRIMARY KEY,
    drug_type VARCHAR(50) NOT NULL,
    quality DECIMAL(3,2),
    quantity DECIMAL(10,2),
    obtained_from VARCHAR(255),
    obtained_at TIMESTAMP DEFAULT NOW(),
    street_value DECIMAL(10,2),
    used_for_empire BOOLEAN DEFAULT FALSE,
    metadata JSONB
);

-- Death records
CREATE TABLE IF NOT EXISTS death_records (
    death_id SERIAL PRIMARY KEY,
    player_id VARCHAR(255),
    corpse_id VARCHAR(255) UNIQUE,
    death_location POINT,
    world VARCHAR(20),
    death_time TIMESTAMP DEFAULT NOW(),
    gear_items JSONB,
    killed_by VARCHAR(255),
    veil_fray_level INT,
    retrieved BOOLEAN DEFAULT FALSE,
    retrieved_at TIMESTAMP,
    bribe_paid JSONB
);

-- Broker's Book entries (player knowledge)
CREATE TABLE IF NOT EXISTS broker_book_knowledge (
    player_id VARCHAR(255),
    entry_type VARCHAR(50),
    entry_id VARCHAR(255),
    knowledge_tier VARCHAR(20),
    unlock_count INT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    entry_data JSONB,
    PRIMARY KEY (player_id, entry_type, entry_id)
);

-- Create indexes
CREATE INDEX idx_body_parts_quality ON body_parts(quality);
CREATE INDEX idx_body_parts_harvested ON body_parts(harvested_at);
CREATE INDEX idx_dark_clients_family ON dark_clients(family);
CREATE INDEX idx_dark_clients_tier ON dark_clients(tier);
CREATE INDEX idx_transactions_client ON broker_transactions(client_id);
CREATE INDEX idx_transactions_date ON broker_transactions(transaction_date);
CREATE INDEX idx_kill_records_player ON kill_records(player_id);
CREATE INDEX idx_kill_records_target_type ON kill_records(target_type);
CREATE INDEX idx_death_records_player ON death_records(player_id);
CREATE INDEX idx_book_knowledge_player ON broker_book_knowledge(player_id);

