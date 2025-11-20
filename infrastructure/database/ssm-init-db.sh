#!/bin/bash
CLUSTER_ENDPOINT="gaming-system-aurora-db-cluster.cluster-cal6eoegigyq.us-east-1.rds.amazonaws.com"
SECRET_ARN="arn:aws:secretsmanager:us-east-1:695353648052:secret:gaming-system-aurora-db-db-credentials-qYLEZ7"
DB_NAME="gaming_system_ai_core"
REGION="us-east-1"

# Get credentials
CREDENTIALS=$(aws secretsmanager get-secret-value --secret-id $SECRET_ARN --region $REGION --query SecretString --output text)
DB_USER=$(echo $CREDENTIALS | jq -r .username)
DB_PASS=$(echo $CREDENTIALS | jq -r .password)

export PGPASSWORD=$DB_PASS

# Create and initialize database
psql -h $CLUSTER_ENDPOINT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Database already exists"

psql -h $CLUSTER_ENDPOINT -U $DB_USER -d $DB_NAME -c "
CREATE SCHEMA IF NOT EXISTS audio_analytics;
CREATE SCHEMA IF NOT EXISTS engagement;
CREATE SCHEMA IF NOT EXISTS localization;
CREATE SCHEMA IF NOT EXISTS language_system;
CREATE SCHEMA IF NOT EXISTS users;
CREATE SCHEMA IF NOT EXISTS ethelred;

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

CREATE TABLE IF NOT EXISTS audio_analytics.archetype_profiles (
    id SERIAL PRIMARY KEY,
    archetype_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    frequency_profile JSONB NOT NULL,
    spectral_characteristics JSONB NOT NULL,
    temporal_patterns JSONB NOT NULL,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO audio_analytics.archetype_profiles 
(archetype_name, description, frequency_profile, spectral_characteristics, temporal_patterns) 
VALUES 
('vampire_alpha', 'Vampire archetype - smooth, hypnotic',
    '{\"low_freq\": 0.3, \"mid_freq\": 0.5, \"high_freq\": 0.2}'::jsonb,
    '{\"resonance\": 0.8, \"breathiness\": 0.2, \"clarity\": 0.9}'::jsonb,
    '{\"cadence\": \"slow\", \"pauses\": \"frequent\", \"emphasis\": \"subtle\"}'::jsonb),
('zombie_beta', 'Zombie archetype - rough, guttural',
    '{\"low_freq\": 0.6, \"mid_freq\": 0.3, \"high_freq\": 0.1}'::jsonb,
    '{\"resonance\": 0.2, \"breathiness\": 0.7, \"clarity\": 0.3}'::jsonb,
    '{\"cadence\": \"irregular\", \"pauses\": \"random\", \"emphasis\": \"harsh\"}'::jsonb),
('werewolf_gamma', 'Werewolf archetype - dynamic, shifting',
    '{\"low_freq\": 0.5, \"mid_freq\": 0.3, \"high_freq\": 0.2}'::jsonb,
    '{\"resonance\": 0.5, \"breathiness\": 0.4, \"clarity\": 0.6}'::jsonb,
    '{\"cadence\": \"variable\", \"pauses\": \"short\", \"emphasis\": \"growling\"}'::jsonb)
ON CONFLICT (archetype_name) DO NOTHING;

CREATE TABLE IF NOT EXISTS engagement.sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds FLOAT,
    events JSONB DEFAULT '[]'::jsonb,
    metrics JSONB DEFAULT '{}'::jsonb,
    addiction_indicators JSONB,
    safety_scores JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users.preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    language_code VARCHAR(10) DEFAULT 'en-US',
    timezone VARCHAR(50) DEFAULT 'UTC',
    audio_quality VARCHAR(20) DEFAULT 'high',
    safety_mode VARCHAR(20) DEFAULT 'moderate',
    engagement_limits JSONB DEFAULT '{}'::jsonb,
    feature_flags JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE VIEW ethelred.audio_metrics AS
SELECT
    id,
    analysis_id,
    user_id,
    session_id,
    sample_rate,
    duration_seconds,
    intelligibility_score,
    confidence_level,
    archetype,
    archetype_matches,
    metadata,
    created_at AS analysis_timestamp,
    updated_at
FROM audio_analytics.audio_metrics;

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

SELECT 'Database initialized successfully' as status,
       COUNT(DISTINCT table_schema) as schemas_created,
       COUNT(*) as tables_created 
FROM information_schema.tables 
WHERE table_schema IN ('audio_analytics', 'engagement', 'users');
"
