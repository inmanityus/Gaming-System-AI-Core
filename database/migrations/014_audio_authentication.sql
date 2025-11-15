-- Audio Authentication & Vocal Simulator QA Tables
-- For tracking audio segment quality metrics and reports

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Audio segments table (R-AUD-IN-002, R-AUD-OUT-001)
CREATE TABLE IF NOT EXISTS audio_segments (
    segment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    build_id VARCHAR(128) NOT NULL,
    segment_type VARCHAR(50) NOT NULL CHECK (segment_type IN ('dialogue', 'monster_vocalization', 'ambient', 'mixed_bus')),
    
    -- Speaker information
    speaker_id VARCHAR(128),
    speaker_role VARCHAR(50) CHECK (speaker_role IN ('npc', 'narrator', 'player')),
    archetype_id VARCHAR(128),
    
    -- Language and context
    language_code VARCHAR(10),
    scene_id VARCHAR(128),
    experience_id VARCHAR(128),
    line_id VARCHAR(128),
    emotional_tag VARCHAR(50),
    environment_type VARCHAR(128),
    
    -- Technical details
    simulator_applied BOOLEAN NOT NULL DEFAULT FALSE,
    media_uri TEXT NOT NULL, -- e.g., "redalert://media/audio/{build_id}/{segment_id}.ogg"
    sample_rate INTEGER,
    bit_depth INTEGER,
    channels INTEGER,
    duration_seconds FLOAT NOT NULL,
    bus_name VARCHAR(128),
    
    -- Timestamps
    timestamp_start TIMESTAMP NOT NULL,
    timestamp_end TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Capture metadata (flexible JSONB for additional fields)
    capture_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Indexes for common queries
    INDEX idx_audio_segments_build (build_id),
    INDEX idx_audio_segments_speaker (speaker_id),
    INDEX idx_audio_segments_archetype (archetype_id),
    INDEX idx_audio_segments_language (language_code),
    INDEX idx_audio_segments_scene (scene_id),
    INDEX idx_audio_segments_timestamp (timestamp_start, timestamp_end)
);

-- Audio scores table (R-AUD-MET-001 through R-AUD-MET-005)
CREATE TABLE IF NOT EXISTS audio_scores (
    segment_id UUID PRIMARY KEY REFERENCES audio_segments(segment_id) ON DELETE CASCADE,
    
    -- Scalar scores (0.0-1.0)
    intelligibility FLOAT CHECK (intelligibility >= 0 AND intelligibility <= 1),
    naturalness FLOAT CHECK (naturalness >= 0 AND naturalness <= 1),
    archetype_conformity FLOAT CHECK (archetype_conformity >= 0 AND archetype_conformity <= 1),
    simulator_stability FLOAT CHECK (simulator_stability >= 0 AND simulator_stability <= 1),
    mix_quality FLOAT CHECK (mix_quality >= 0 AND mix_quality <= 1),
    
    -- Band classifications
    intelligibility_band VARCHAR(50) CHECK (intelligibility_band IN ('acceptable', 'degraded', 'unacceptable')),
    naturalness_band VARCHAR(50) CHECK (naturalness_band IN ('ok', 'robotic', 'monotone')),
    archetype_band VARCHAR(50) CHECK (archetype_band IN ('on_profile', 'too_clean', 'too_flat', 'misaligned')),
    stability_band VARCHAR(50) CHECK (stability_band IN ('stable', 'unstable')),
    mix_quality_band VARCHAR(50) CHECK (mix_quality_band IN ('ok', 'noisy', 'clipping', 'unbalanced')),
    
    -- Additional metrics (flexible)
    additional_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Analysis metadata
    analyzed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    analysis_version VARCHAR(50),
    
    -- Evidence references (for debugging/review)
    evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb
);

-- Audio archetype reports table (R-AUD-OUT-002)
CREATE TABLE IF NOT EXISTS audio_archetype_reports (
    report_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    build_id VARCHAR(128) NOT NULL,
    archetype_id VARCHAR(128),
    language_code VARCHAR(10),
    scene_id VARCHAR(128),
    report_type VARCHAR(50) NOT NULL CHECK (report_type IN ('archetype_report', 'language_report', 'scene_report', 'build_report')),
    
    -- Summary statistics
    num_segments INTEGER NOT NULL,
    intelligibility_distribution JSONB NOT NULL DEFAULT '{}'::jsonb,
    naturalness_mean FLOAT,
    archetype_conformity_mean FLOAT,
    simulator_stability_mean FLOAT,
    mix_quality_mean FLOAT,
    
    -- Analysis results
    common_deviations TEXT[],
    
    -- Comparison with previous build
    prev_build_id VARCHAR(128),
    archetype_conformity_delta FLOAT,
    simulator_stability_delta FLOAT,
    intelligibility_delta FLOAT,
    comparison_notes TEXT,
    
    -- Metadata
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Indexes
    INDEX idx_audio_reports_build (build_id),
    INDEX idx_audio_reports_archetype (archetype_id),
    INDEX idx_audio_reports_language (language_code)
);

-- Audio feedback table (R-AUD-FB-001, R-AUD-FB-002)
CREATE TABLE IF NOT EXISTS audio_feedback (
    feedback_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    build_id VARCHAR(128) NOT NULL,
    feedback_type VARCHAR(50) NOT NULL CHECK (feedback_type IN ('simulator', 'archetype')),
    
    -- Target of feedback
    archetype_id VARCHAR(128),
    simulator_profile_id VARCHAR(128),
    language_code VARCHAR(10),
    
    -- Feedback content (structured)
    findings JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommendations TEXT[],
    notes TEXT,
    
    -- For archetype feedback
    mean_archetype_conformity FLOAT,
    weak_contexts TEXT[],
    candidate_training_examples JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    -- Metadata
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    applied BOOLEAN DEFAULT FALSE,
    applied_at TIMESTAMP,
    
    INDEX idx_audio_feedback_build (build_id),
    INDEX idx_audio_feedback_archetype (archetype_id)
);

-- Audio red alerts table (R-AUD-OUT-003)
CREATE TABLE IF NOT EXISTS audio_red_alerts (
    alert_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    build_id VARCHAR(128) NOT NULL,
    alert_type VARCHAR(128) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('warning', 'error', 'critical')),
    
    -- Alert details
    description TEXT NOT NULL,
    affected_segment_ids UUID[],
    affected_scene_ids VARCHAR(128)[],
    affected_archetype_id VARCHAR(128),
    
    -- Triggering metrics
    triggering_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Status
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(128),
    acknowledged_at TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    
    INDEX idx_audio_alerts_build (build_id),
    INDEX idx_audio_alerts_type (alert_type),
    INDEX idx_audio_alerts_severity (severity)
);

-- Human speech baseline profiles (reference data)
CREATE TABLE IF NOT EXISTS audio_speech_baselines (
    baseline_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    language_code VARCHAR(10) NOT NULL,
    corpus_source VARCHAR(128), -- e.g., 'LibriSpeech', 'CommonVoice', 'VCTK'
    
    -- Language-specific norms
    speech_rate_mean FLOAT,
    speech_rate_std FLOAT,
    pitch_mean_hz FLOAT,
    pitch_std_hz FLOAT,
    prosodic_variability JSONB NOT NULL DEFAULT '{}'::jsonb,
    articulation_clarity JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(language_code, corpus_source)
);

-- Archetype voice profiles (reference data)
CREATE TABLE IF NOT EXISTS audio_archetype_profiles (
    profile_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    archetype_id VARCHAR(128) NOT NULL,
    profile_version VARCHAR(50) NOT NULL,
    
    -- Target acoustic characteristics
    f0_range_min FLOAT,
    f0_range_max FLOAT,
    f0_variability_target FLOAT,
    formant_distribution JSONB NOT NULL DEFAULT '{}'::jsonb,
    roughness_target FLOAT,
    breathiness_target FLOAT,
    corruption_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Context-specific variations
    context_variations JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Status
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(archetype_id, profile_version),
    INDEX idx_audio_profiles_active (archetype_id, active)
);

-- Indexes for performance
CREATE INDEX idx_audio_segments_build_type ON audio_segments(build_id, segment_type);
CREATE INDEX idx_audio_scores_bands ON audio_scores(intelligibility_band, naturalness_band, archetype_band);
CREATE INDEX idx_audio_segments_created ON audio_segments(created_at);

-- Data retention comment
COMMENT ON TABLE audio_segments IS 'Audio segment metadata and references. Actual audio files are stored in media storage with configurable retention.';
COMMENT ON TABLE audio_scores IS 'Per-segment quality metrics. Retained for trend analysis across builds.';
COMMENT ON TABLE audio_archetype_reports IS 'Aggregated reports by archetype/language/scene. Used for build-over-build comparisons.';
COMMENT ON COLUMN audio_segments.media_uri IS 'Reference to audio file in Red Alert media storage. Files follow separate retention policy.';
COMMENT ON COLUMN audio_feedback.applied IS 'Tracks whether feedback has been reviewed and applied. No automatic application per safety requirements.';
