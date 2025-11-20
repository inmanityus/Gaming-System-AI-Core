-- Gaming System AI Core Database Setup
-- This script creates the complete database structure for the gaming system

-- Drop existing database if needed (for clean setup)
-- DROP DATABASE IF EXISTS gaming_system_ai_core;

-- Create the main database
CREATE DATABASE gaming_system_ai_core
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    CONNECTION LIMIT = -1;

-- Connect to the new database
\c gaming_system_ai_core;

-- Create schemas for different domains
CREATE SCHEMA IF NOT EXISTS audio_analytics;
CREATE SCHEMA IF NOT EXISTS engagement;
CREATE SCHEMA IF NOT EXISTS localization;
CREATE SCHEMA IF NOT EXISTS language_system;
CREATE SCHEMA IF NOT EXISTS users;
CREATE SCHEMA IF NOT EXISTS ethelred;  -- Legacy compatibility

-- Set search path to include all schemas
SET search_path TO audio_analytics, engagement, localization, language_system, users, ethelred, public;

-- ==========================================
-- Audio Analytics Schema
-- ==========================================

-- Audio metrics table
CREATE TABLE audio_analytics.audio_metrics (
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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audio_metrics_user_session (user_id, session_id),
    INDEX idx_audio_metrics_analysis_id (analysis_id),
    INDEX idx_audio_metrics_created_at (created_at DESC)
);

-- Archetype profiles table
CREATE TABLE audio_analytics.archetype_profiles (
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

-- ==========================================
-- Engagement Schema
-- ==========================================

-- Engagement sessions table
CREATE TABLE engagement.sessions (
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sessions_user_id (user_id),
    INDEX idx_sessions_start_time (start_time DESC)
);

-- User preferences table
CREATE TABLE users.preferences (
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

-- ==========================================
-- Localization Schema
-- ==========================================

-- Localized content table
CREATE TABLE localization.content (
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
    UNIQUE(content_key, language_code, version),
    INDEX idx_content_key_lang (content_key, language_code)
);

-- Language statistics table
CREATE TABLE localization.language_stats (
    id SERIAL PRIMARY KEY,
    language_code VARCHAR(10) NOT NULL,
    total_keys INTEGER DEFAULT 0,
    translated_keys INTEGER DEFAULT 0,
    coverage_percent FLOAT DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(language_code)
);

-- ==========================================
-- Language System Schema
-- ==========================================

-- TTS cache table
CREATE TABLE language_system.tts_cache (
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tts_cache_key (cache_key),
    INDEX idx_tts_last_accessed (last_accessed)
);

-- TTS metrics table
CREATE TABLE language_system.tts_metrics (
    id SERIAL PRIMARY KEY,
    request_id UUID NOT NULL DEFAULT gen_random_uuid(),
    language_code VARCHAR(10) NOT NULL,
    voice_id VARCHAR(100),
    text_length INTEGER NOT NULL,
    processing_time_ms FLOAT NOT NULL,
    cache_hit BOOLEAN DEFAULT false,
    error_occurred BOOLEAN DEFAULT false,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tts_metrics_created (created_at DESC)
);

-- ==========================================
-- Legacy Ethelred Schema (for compatibility)
-- ==========================================

-- Mirror of audio_metrics for backward compatibility
CREATE VIEW ethelred.audio_metrics AS
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

-- ==========================================
-- Functions and Triggers
-- ==========================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to all tables with updated_at
CREATE TRIGGER update_audio_metrics_updated_at BEFORE UPDATE ON audio_analytics.audio_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_archetype_profiles_updated_at BEFORE UPDATE ON audio_analytics.archetype_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_preferences_updated_at BEFORE UPDATE ON users.preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_content_updated_at BEFORE UPDATE ON localization.content
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- Initial Data
-- ==========================================

-- Insert default archetype profiles
INSERT INTO audio_analytics.archetype_profiles (archetype_name, description, frequency_profile, spectral_characteristics, temporal_patterns) VALUES
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
    '{"cadence": "variable", "pauses": "short", "emphasis": "growling"}'::jsonb);

-- Insert default language support
INSERT INTO localization.language_stats (language_code, total_keys, translated_keys, coverage_percent) VALUES
('en-US', 100, 100, 100.0),
('es-ES', 100, 85, 85.0),
('fr-FR', 100, 78, 78.0),
('de-DE', 100, 72, 72.0),
('ja-JP', 100, 65, 65.0),
('zh-CN', 100, 60, 60.0);

-- Grant permissions
GRANT USAGE ON SCHEMA audio_analytics, engagement, localization, language_system, users, ethelred TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA audio_analytics, engagement, localization, language_system, users, ethelred TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA audio_analytics, engagement, localization, language_system, users, ethelred TO postgres;

-- Create indexes for performance
CREATE INDEX idx_audio_metrics_user_created ON audio_analytics.audio_metrics(user_id, created_at DESC);
CREATE INDEX idx_sessions_user_start ON engagement.sessions(user_id, start_time DESC);
CREATE INDEX idx_content_lang_approved ON localization.content(language_code, approved) WHERE approved = true;

-- Add comments for documentation
COMMENT ON DATABASE gaming_system_ai_core IS 'Main database for Gaming System AI Core - Audio, Engagement, and Language Analytics';
COMMENT ON SCHEMA audio_analytics IS 'Audio analysis metrics and archetype matching';
COMMENT ON SCHEMA engagement IS 'User engagement tracking and addiction monitoring';
COMMENT ON SCHEMA localization IS 'Multi-language content management';
COMMENT ON SCHEMA language_system IS 'TTS and language processing cache';
COMMENT ON SCHEMA users IS 'User preferences and settings';
COMMENT ON SCHEMA ethelred IS 'Legacy compatibility views for existing code';
