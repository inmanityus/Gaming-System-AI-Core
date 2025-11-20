#!/bin/bash
# Aurora database initialization script to run via SSM

# Aurora connection details
AURORA_ENDPOINT="gaming-system-aurora-db-cluster.cluster-cal6eoegigyq.us-east-1.rds.amazonaws.com"
DB_NAME="gaming_system_ai_core"
SECRET_ARN="arn:aws:secretsmanager:us-east-1:695353648052:secret:gaming-system-aurora-db-db-credentials-qYLEZ7"

# Get credentials from Secrets Manager
echo "Retrieving database credentials..."
SECRET_JSON=$(aws secretsmanager get-secret-value --secret-id "$SECRET_ARN" --query SecretString --output text --region us-east-1)
DB_USER=$(echo $SECRET_JSON | jq -r '.username')
DB_PASSWORD=$(echo $SECRET_JSON | jq -r '.password')

export PGPASSWORD=$DB_PASSWORD

# Test connection
echo "Testing database connection..."
psql -h "$AURORA_ENDPOINT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();"

if [ $? -eq 0 ]; then
    echo "Connection successful!"
    
    # Create schemas and tables
    echo "Creating database schema..."
    
    psql -h "$AURORA_ENDPOINT" -U "$DB_USER" -d "$DB_NAME" <<'EOF'
-- Create schemas for different domains
CREATE SCHEMA IF NOT EXISTS audio_analytics;
CREATE SCHEMA IF NOT EXISTS engagement;
CREATE SCHEMA IF NOT EXISTS localization;
CREATE SCHEMA IF NOT EXISTS language_system;
CREATE SCHEMA IF NOT EXISTS users;
CREATE SCHEMA IF NOT EXISTS ethelred;

-- Set search path
SET search_path TO audio_analytics, engagement, localization, language_system, users, ethelred, public;

-- Audio Analytics Schema
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
CREATE INDEX IF NOT EXISTS idx_audio_metrics_analysis_id ON audio_analytics.audio_metrics(analysis_id);
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

-- Engagement Schema
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

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON engagement.sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON engagement.sessions(start_time DESC);

-- User Preferences
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

-- Localization Schema
CREATE TABLE IF NOT EXISTS localization.content (
    id SERIAL PRIMARY KEY,
    content_key VARCHAR(255) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    content_value TEXT NOT NULL,
    context VARCHAR(100),
    version INTEGER DEFAULT 1,
    approved BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(content_key, language_code, version)
);

CREATE INDEX IF NOT EXISTS idx_content_key_lang ON localization.content(content_key, language_code);

CREATE TABLE IF NOT EXISTS localization.language_stats (
    id SERIAL PRIMARY KEY,
    language_code VARCHAR(10) NOT NULL,
    total_keys INTEGER DEFAULT 0,
    translated_keys INTEGER DEFAULT 0,
    coverage_percent FLOAT DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(language_code)
);

-- Language System Schema
CREATE TABLE IF NOT EXISTS language_system.tts_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(64) NOT NULL UNIQUE,
    text_input TEXT NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    voice_id VARCHAR(100),
    audio_format VARCHAR(20) DEFAULT 'wav',
    audio_data BYTEA,
    file_path TEXT,
    duration_seconds FLOAT,
    metadata JSONB DEFAULT '{}'::jsonb,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tts_cache_key ON language_system.tts_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_tts_last_accessed ON language_system.tts_cache(last_accessed);

CREATE TABLE IF NOT EXISTS language_system.tts_metrics (
    id SERIAL PRIMARY KEY,
    request_id UUID NOT NULL DEFAULT gen_random_uuid(),
    language_code VARCHAR(10) NOT NULL,
    voice_id VARCHAR(100),
    text_length INTEGER NOT NULL,
    processing_time_ms FLOAT NOT NULL,
    cache_hit BOOLEAN DEFAULT false,
    error_occurred BOOLEAN DEFAULT false,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tts_metrics_created ON language_system.tts_metrics(created_at DESC);

-- Legacy Ethelred compatibility view
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

-- Update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_audio_metrics_updated_at') THEN
        CREATE TRIGGER update_audio_metrics_updated_at BEFORE UPDATE ON audio_analytics.audio_metrics
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_archetype_profiles_updated_at') THEN
        CREATE TRIGGER update_archetype_profiles_updated_at BEFORE UPDATE ON audio_analytics.archetype_profiles
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_preferences_updated_at') THEN
        CREATE TRIGGER update_preferences_updated_at BEFORE UPDATE ON users.preferences
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_content_updated_at') THEN
        CREATE TRIGGER update_content_updated_at BEFORE UPDATE ON localization.content
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END$$;

-- Insert initial data
INSERT INTO audio_analytics.archetype_profiles (archetype_name, description, frequency_profile, spectral_characteristics, temporal_patterns)
VALUES 
    ('vampire_alpha', 'Vampire archetype - smooth, hypnotic',
        '{"low_freq": 0.3, "mid_freq": 0.5, "high_freq": 0.2}'::jsonb,
        '{"resonance": 0.8, "breathiness": 0.2, "clarity": 0.9}'::jsonb,
        '{"cadence": "slow", "pauses": "frequent", "emphasis": "subtle"}'::jsonb),
    ('zombie_beta', 'Zombie archetype - rough, guttural',
        '{"low_freq": 0.6, "mid_freq": 0.3, "high_freq": 0.1}'::jsonb,
        '{"resonance": 0.2, "breathiness": 0.7, "clarity": 0.3}'::jsonb,
        '{"cadence": "irregular", "pauses": "random", "emphasis": "harsh"}'::jsonb),
    ('werewolf_gamma', 'Werewolf archetype - dynamic, shifting',
        '{"low_freq": 0.5, "mid_freq": 0.3, "high_freq": 0.2}'::jsonb,
        '{"resonance": 0.5, "breathiness": 0.4, "clarity": 0.6}'::jsonb,
        '{"cadence": "variable", "pauses": "short", "emphasis": "growling"}'::jsonb)
ON CONFLICT (archetype_name) DO NOTHING;

INSERT INTO localization.language_stats (language_code, total_keys, translated_keys, coverage_percent)
VALUES
    ('en-US', 100, 100, 100.0),
    ('es-ES', 100, 85, 85.0),
    ('fr-FR', 100, 78, 78.0),
    ('de-DE', 100, 72, 72.0),
    ('ja-JP', 100, 65, 65.0),
    ('zh-CN', 100, 60, 60.0)
ON CONFLICT (language_code) DO NOTHING;

-- Show summary
SELECT 
    schema_name,
    COUNT(*) as table_count
FROM information_schema.tables
WHERE table_schema IN ('audio_analytics', 'engagement', 'localization', 'language_system', 'users')
GROUP BY schema_name
ORDER BY schema_name;

EOF

    if [ $? -eq 0 ]; then
        echo "Database initialization completed successfully!"
    else
        echo "Error during database initialization"
        exit 1
    fi
else
    echo "Failed to connect to database"
    exit 1
fi

echo "Database setup complete!"
