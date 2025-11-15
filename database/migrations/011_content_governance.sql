-- Content Governance & Content Levels Schema
-- Migration: 011_content_governance.sql
-- Date: 2025-11-15
--
-- Implements core tables required for ETHELRED Content Governance Milestones 1–2:
--   - content_levels            (profile registry)
--   - player_content_profiles   (per-player policy)
--   - session_content_policy    (per-session snapshots)
--   - content_violations        (runtime violations log)

-- ============================================================================
-- CONTENT LEVEL PROFILES
-- ============================================================================
CREATE TABLE IF NOT EXISTS content_levels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,

    -- Per-category allowed levels (0 = none, 4 = extreme)
    violence_gore_level SMALLINT NOT NULL CHECK (violence_gore_level BETWEEN 0 AND 4),
    sexual_content_nudity_level SMALLINT NOT NULL CHECK (sexual_content_nudity_level BETWEEN 0 AND 4),
    language_profanity_level SMALLINT NOT NULL CHECK (language_profanity_level BETWEEN 0 AND 4),
    horror_intensity_level SMALLINT NOT NULL CHECK (horror_intensity_level BETWEEN 0 AND 4),
    drugs_substances_level SMALLINT NOT NULL CHECK (drugs_substances_level BETWEEN 0 AND 4),
    sensitive_themes_level SMALLINT NOT NULL CHECK (sensitive_themes_level BETWEEN 0 AND 4),
    moral_complexity_level SMALLINT NOT NULL CHECK (moral_complexity_level BETWEEN 0 AND 4),

    -- Arbitrary per-theme flags for sensitive topics
    sensitive_themes_flags JSONB NOT NULL DEFAULT '{}'::jsonb,

    is_system_default BOOLEAN NOT NULL DEFAULT FALSE,
    target_age_rating VARCHAR(10),
    created_by VARCHAR(100),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_content_levels_is_system_default
    ON content_levels(is_system_default);

CREATE INDEX IF NOT EXISTS idx_content_levels_target_age_rating
    ON content_levels(target_age_rating);

-- ============================================================================
-- PER-PLAYER CONTENT POLICY
-- ============================================================================
CREATE TABLE IF NOT EXISTS player_content_profiles (
    player_id UUID PRIMARY KEY REFERENCES players(id) ON DELETE CASCADE,
    base_level_id UUID NOT NULL REFERENCES content_levels(id),

    -- Per-category overrides applied on top of the base profile
    overrides JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Arbitrary JSON rules (e.g., { "skip_torture_scenes": true })
    custom_rules JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_player_content_profiles_base_level
    ON player_content_profiles(base_level_id);

-- ============================================================================
-- PER-SESSION CONTENT POLICY SNAPSHOTS
-- ============================================================================
CREATE TABLE IF NOT EXISTS session_content_policy (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL,
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    base_level_id UUID NOT NULL REFERENCES content_levels(id),

    -- Fully resolved per-category levels used for this session
    effective_levels JSONB NOT NULL,

    -- Overrides and custom rules at the time of snapshot
    overrides JSONB NOT NULL DEFAULT '{}'::jsonb,
    custom_rules JSONB NOT NULL DEFAULT '{}'::jsonb,

    policy_version INTEGER NOT NULL DEFAULT 1,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_session_content_policy_session
    ON session_content_policy(session_id);

CREATE INDEX IF NOT EXISTS idx_session_content_policy_player
    ON session_content_policy(player_id);

-- Ensure policy_version is unique per session
CREATE UNIQUE INDEX IF NOT EXISTS uq_session_content_policy_session_version
    ON session_content_policy(session_id, policy_version);

-- ============================================================================
-- CONTENT VIOLATIONS LOG
-- ============================================================================
CREATE TABLE IF NOT EXISTS content_violations (
    violation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    session_id UUID,
    player_id UUID REFERENCES players(id) ON DELETE SET NULL,

    content_type VARCHAR(50) NOT NULL,  -- story_output, npc_dialogue, visual_scene, audio_segment, etc.
    category VARCHAR(64) NOT NULL,      -- violence_gore, horror_intensity, etc.

    expected_level SMALLINT NOT NULL CHECK (expected_level BETWEEN 0 AND 4),
    observed_level SMALLINT NOT NULL CHECK (observed_level BETWEEN 0 AND 4),

    severity VARCHAR(20) NOT NULL,      -- low, medium, high, critical
    action_taken VARCHAR(100),
    detected_by VARCHAR(64) NOT NULL,   -- guardrails_monitor, ethelred_content_validator, etc.

    flagged_excerpt TEXT,
    context JSONB NOT NULL DEFAULT '{}'::jsonb,

    build_id VARCHAR(64),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_content_violations_session
    ON content_violations(session_id);

CREATE INDEX IF NOT EXISTS idx_content_violations_player
    ON content_violations(player_id);

CREATE INDEX IF NOT EXISTS idx_content_violations_category
    ON content_violations(category);

CREATE INDEX IF NOT EXISTS idx_content_violations_severity
    ON content_violations(severity);

-- ============================================================================
-- UPDATED_AT TRIGGERS
-- ============================================================================
-- Reuse the global update_updated_at_column() trigger function defined in
-- 001_initial_schema.sql to keep updated_at in sync.

CREATE TRIGGER update_content_levels_updated_at
    BEFORE UPDATE ON content_levels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_player_content_profiles_updated_at
    BEFORE UPDATE ON player_content_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_session_content_policy_updated_at
    BEFORE UPDATE ON session_content_policy
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_content_violations_updated_at
    BEFORE UPDATE ON content_violations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


