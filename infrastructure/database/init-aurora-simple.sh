#!/bin/bash
# Simple Aurora database initialization script

echo "Starting database initialization..."

# Get credentials
SECRET=$(aws secretsmanager get-secret-value --secret-id arn:aws:secretsmanager:us-east-1:695353648052:secret:gaming-system-aurora-db-db-credentials-qYLEZ7 --query SecretString --output text)
DB_USER=$(echo $SECRET | jq -r .username)
DB_PASS=$(echo $SECRET | jq -r .password)
DB_HOST="gaming-system-aurora-db-cluster.cluster-cal6eoegigyq.us-east-1.rds.amazonaws.com"

export PGPASSWORD=$DB_PASS

# Create database
echo "Creating database..."
psql -h $DB_HOST -U $DB_USER -d postgres -c "CREATE DATABASE gaming_system_ai_core;" 2>/dev/null || echo "Database already exists"

# Create schemas and tables
echo "Creating schemas and tables..."
psql -h $DB_HOST -U $DB_USER -d gaming_system_ai_core <<'EOF'
-- Create schemas
CREATE SCHEMA IF NOT EXISTS audio_analytics;
CREATE SCHEMA IF NOT EXISTS engagement;
CREATE SCHEMA IF NOT EXISTS users;
CREATE SCHEMA IF NOT EXISTS ethelred;

-- Audio metrics table
CREATE TABLE IF NOT EXISTS audio_analytics.audio_metrics (
    id SERIAL PRIMARY KEY,
    analysis_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    sample_rate INTEGER NOT NULL CHECK (sample_rate > 0),
    duration_seconds FLOAT NOT NULL CHECK (duration_seconds > 0),
    intelligibility_score FLOAT NOT NULL CHECK (intelligibility_score >= 0 AND intelligibility_score <= 1),
    confidence_level FLOAT CHECK (confidence_level >= 0 AND confidence_level <= 1),
    archetype VARCHAR(100),
    archetype_matches JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audio_metrics_user_session ON audio_analytics.audio_metrics(user_id, session_id);
CREATE INDEX IF NOT EXISTS idx_audio_metrics_created_at ON audio_analytics.audio_metrics(created_at DESC);

-- Archetype profiles
CREATE TABLE IF NOT EXISTS audio_analytics.archetype_profiles (
    id SERIAL PRIMARY KEY,
    archetype_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    frequency_profile JSONB NOT NULL,
    spectral_characteristics JSONB NOT NULL,
    temporal_patterns JSONB NOT NULL,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert archetype profiles
INSERT INTO audio_analytics.archetype_profiles 
(archetype_name, description, frequency_profile, spectral_characteristics, temporal_patterns) 
VALUES 
('vampire_alpha', 'Vampire archetype', '{"low_freq": 0.3, "mid_freq": 0.5, "high_freq": 0.2}'::jsonb, '{"resonance": 0.8}'::jsonb, '{"cadence": "slow"}'::jsonb),
('zombie_beta', 'Zombie archetype', '{"low_freq": 0.6, "mid_freq": 0.3, "high_freq": 0.1}'::jsonb, '{"resonance": 0.2}'::jsonb, '{"cadence": "irregular"}'::jsonb),
('werewolf_gamma', 'Werewolf archetype', '{"low_freq": 0.5, "mid_freq": 0.3, "high_freq": 0.2}'::jsonb, '{"resonance": 0.5}'::jsonb, '{"cadence": "variable"}'::jsonb)
ON CONFLICT (archetype_name) DO NOTHING;

-- Insert test data
INSERT INTO audio_analytics.audio_metrics 
(user_id, session_id, sample_rate, duration_seconds, intelligibility_score, confidence_level, archetype, metadata)
SELECT 
    'test_user_perf',
    'session_' || generate_series,
    48000,
    3.5,
    0.75 + (random() * 0.2),
    0.8 + (random() * 0.15),
    CASE (generate_series % 3)
        WHEN 0 THEN 'vampire_alpha'
        WHEN 1 THEN 'zombie_beta'
        ELSE 'werewolf_gamma'
    END,
    jsonb_build_object('test', true, 'index', generate_series)
FROM generate_series(1, 100)
ON CONFLICT (analysis_id) DO NOTHING;

-- Create view
CREATE OR REPLACE VIEW ethelred.audio_metrics AS
SELECT * FROM audio_analytics.audio_metrics;

-- Verify
SELECT COUNT(*) AS record_count FROM audio_analytics.audio_metrics;
SELECT COUNT(*) AS profile_count FROM audio_analytics.archetype_profiles;
EOF

echo "Database initialization complete!"
