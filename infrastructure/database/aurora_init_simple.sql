-- Gaming System AI Core Database Schema
-- Aurora PostgreSQL initialization

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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User Preferences
CREATE TABLE IF NOT EXISTS users.preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    language_code VARCHAR(10) DEFAULT 'en-US',
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Localization Schema
CREATE TABLE IF NOT EXISTS localization.content (
    id SERIAL PRIMARY KEY,
    content_key VARCHAR(255) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    content_value TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(content_key, language_code)
);

-- Language System Schema
CREATE TABLE IF NOT EXISTS language_system.tts_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(64) NOT NULL UNIQUE,
    text_input TEXT NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Legacy compatibility view
CREATE OR REPLACE VIEW ethelred.audio_metrics AS
SELECT * FROM audio_analytics.audio_metrics;

-- Insert initial archetype data
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
