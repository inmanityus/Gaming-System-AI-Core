#!/bin/bash
# Initialize Aurora database via SSM

# Install required tools
sudo yum install -y postgresql15 jq

# Configuration
CLUSTER_ENDPOINT="gaming-system-aurora-db-cluster.cluster-cal6eoegigyq.us-east-1.rds.amazonaws.com"
SECRET_ARN="arn:aws:secretsmanager:us-east-1:695353648052:secret:gaming-system-aurora-db-db-credentials-qYLEZ7"
DB_NAME="gaming_system_ai_core"
REGION="us-east-1"

# Get credentials
CREDENTIALS=$(aws secretsmanager get-secret-value --secret-id $SECRET_ARN --region $REGION --query SecretString --output text)
DB_USER=$(echo $CREDENTIALS | jq -r .username)
DB_PASS=$(echo $CREDENTIALS | jq -r .password)

export PGPASSWORD=$DB_PASS

# Create database
psql -h $CLUSTER_ENDPOINT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Database already exists"

# Initialize schema
psql -h $CLUSTER_ENDPOINT -U $DB_USER -d $DB_NAME <<'EOF'
-- Create schemas
CREATE SCHEMA IF NOT EXISTS audio_analytics;
CREATE SCHEMA IF NOT EXISTS engagement;
CREATE SCHEMA IF NOT EXISTS localization;
CREATE SCHEMA IF NOT EXISTS language_system;
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

-- Archetype profiles table
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

-- Insert default archetype profiles
INSERT INTO audio_analytics.archetype_profiles 
(archetype_name, description, frequency_profile, spectral_characteristics, temporal_patterns) 
VALUES 
('vampire_alpha', 'Vampire archetype - smooth, hypnotic',
    '{"low_freq": 0.3, "mid_freq": 0.5, "high_freq": 0.2}'::jsonb,
    '{"resonance": 0.8, "breathiness": 0.2, "clarity": 0.9}'::jsonb,
    '{"cadence": "slow", "pauses": "frequent", "emphasis": "subtle"}'::jsonb)
ON CONFLICT (archetype_name) DO NOTHING;

-- Verify
SELECT COUNT(*) as tables_created FROM information_schema.tables WHERE table_schema = 'audio_analytics';
EOF

echo "Database initialization complete!"
