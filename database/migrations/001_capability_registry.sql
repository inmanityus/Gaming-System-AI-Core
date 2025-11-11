-- database/migrations/001_capability_registry.sql
-- Capability Registry Database Schema
-- Tracks UE5 version capabilities for Storyteller integration

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Feature categories
CREATE TABLE IF NOT EXISTS feature_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Features
CREATE TABLE IF NOT EXISTS features (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category_id INTEGER REFERENCES feature_categories(id),
    description TEXT,
    documentation_url TEXT,
    example_usage TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- UE5 Versions
CREATE TABLE IF NOT EXISTS ue_versions (
    version VARCHAR(10) PRIMARY KEY,
    release_date DATE,
    is_preview BOOLEAN DEFAULT FALSE,
    is_stable BOOLEAN DEFAULT TRUE,
    release_notes_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Version Features (many-to-many)
CREATE TABLE IF NOT EXISTS version_features (
    version VARCHAR(10) REFERENCES ue_versions(version),
    feature_id INTEGER REFERENCES features(id),
    introduced_in VARCHAR(10),
    deprecated_in VARCHAR(10),
    config JSONB,
    PRIMARY KEY (version, feature_id)
);

-- Feature Parameters (for Storyteller prompts)
CREATE TABLE IF NOT EXISTS feature_parameters (
    feature_id INTEGER REFERENCES features(id),
    parameter_name VARCHAR(50),
    parameter_type VARCHAR(20),  -- 'boolean', 'number', 'string', 'enum'
    default_value TEXT,
    description TEXT,
    PRIMARY KEY (feature_id, parameter_name)
);

-- Insert default categories
INSERT INTO feature_categories (name, description) VALUES
    ('rendering', 'Rendering features like Nanite, Lumen, Path Tracer'),
    ('audio', 'Audio features like MetaSound, Spatial Audio'),
    ('physics', 'Physics features like Chaos, Cloth, Fluids'),
    ('ai', 'AI features like Mass AI, Behavior Trees'),
    ('world_building', 'World building features like World Partition, Data Layers'),
    ('animation', 'Animation features like Control Rig, IK Retargeter')
ON CONFLICT (name) DO NOTHING;

-- Insert UE5.6.1 base version
INSERT INTO ue_versions (version, release_date, is_stable) VALUES
    ('5.6.1', '2024-01-01', TRUE)
ON CONFLICT (version) DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_version_features_version ON version_features(version);
CREATE INDEX IF NOT EXISTS idx_version_features_feature ON version_features(feature_id);
CREATE INDEX IF NOT EXISTS idx_features_category ON features(category_id);




