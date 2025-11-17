-- Multi-Language Localization Tables
-- For managing localized strings across the game
-- Implements TML-01 (R-ML-STORE-001, R-ML-STORE-002, R-ML-STORE-003)

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Localization entries table (R-ML-STORE-001)
CREATE TABLE IF NOT EXISTS localization_entries (
    entry_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) NOT NULL,
    language_code VARCHAR(10) NOT NULL, -- e.g., 'en-US', 'ja-JP', 'zh-CN'
    text TEXT NOT NULL,
    
    -- Categorization and metadata
    category VARCHAR(64) NOT NULL CHECK (category IN ('ui', 'narrative', 'system', 'tutorial', 'item', 'character', 'location', 'quest')),
    context TEXT, -- Additional context for translators
    description TEXT, -- What this string represents
    tags TEXT[], -- Additional tags for filtering/searching
    
    -- Plural and gender support
    plural_forms JSONB NOT NULL DEFAULT '{}', -- e.g., {"one": "1 item", "other": "%d items"}
    gender_forms JSONB NOT NULL DEFAULT '{}', -- e.g., {"masculine": "He went", "feminine": "She went"}
    
    -- Version control
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(128),
    
    -- Status tracking
    status VARCHAR(32) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'approved', 'outdated')),
    approved_by VARCHAR(128),
    approved_at TIMESTAMP,
    
    -- Unique constraint on key + language combination
    UNIQUE(key, language_code),
    
    -- Indexes for performance
    INDEX idx_localization_key (key),
    INDEX idx_localization_language (language_code),
    INDEX idx_localization_category (category),
    INDEX idx_localization_status (status),
    INDEX idx_localization_tags USING gin(tags)
);

-- Language preferences table (R-ML-PREF-001)
CREATE TABLE IF NOT EXISTS language_preferences (
    player_id UUID PRIMARY KEY,
    ui_language VARCHAR(10) NOT NULL DEFAULT 'en-US',
    subtitle_language VARCHAR(10),
    voice_language VARCHAR(10),
    
    -- Fallback preferences
    fallback_to_english BOOLEAN NOT NULL DEFAULT TRUE,
    show_original_on_missing BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Accessibility
    use_dyslexia_font BOOLEAN NOT NULL DEFAULT FALSE,
    subtitle_size VARCHAR(20) DEFAULT 'medium' CHECK (subtitle_size IN ('small', 'medium', 'large', 'extra-large')),
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_language_pref_ui (ui_language),
    INDEX idx_language_pref_subtitle (subtitle_language),
    INDEX idx_language_pref_voice (voice_language)
);

-- Localization coverage tracking (R-ML-MET-001)
CREATE TABLE IF NOT EXISTS localization_coverage (
    coverage_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    build_id VARCHAR(128) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    category VARCHAR(64) NOT NULL,
    
    -- Coverage metrics
    total_keys INTEGER NOT NULL DEFAULT 0,
    translated_keys INTEGER NOT NULL DEFAULT 0,
    reviewed_keys INTEGER NOT NULL DEFAULT 0,
    approved_keys INTEGER NOT NULL DEFAULT 0,
    
    -- Quality metrics
    missing_strings INTEGER NOT NULL DEFAULT 0,
    placeholder_mismatches INTEGER NOT NULL DEFAULT 0,
    formatting_errors INTEGER NOT NULL DEFAULT 0,
    
    -- Calculated coverage percentages
    translation_coverage FLOAT GENERATED ALWAYS AS 
        (CASE WHEN total_keys > 0 THEN translated_keys::float / total_keys * 100 ELSE 0 END) STORED,
    review_coverage FLOAT GENERATED ALWAYS AS 
        (CASE WHEN total_keys > 0 THEN reviewed_keys::float / total_keys * 100 ELSE 0 END) STORED,
    approval_coverage FLOAT GENERATED ALWAYS AS 
        (CASE WHEN total_keys > 0 THEN approved_keys::float / total_keys * 100 ELSE 0 END) STORED,
    
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(build_id, language_code, category),
    INDEX idx_coverage_build (build_id),
    INDEX idx_coverage_language (language_code),
    INDEX idx_coverage_category (category)
);

-- Localization issues tracking (R-ML-QA-003)
CREATE TABLE IF NOT EXISTS localization_issues (
    issue_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    build_id VARCHAR(128),
    
    -- Issue details
    issue_type VARCHAR(64) NOT NULL CHECK (issue_type IN (
        'missing_translation', 'placeholder_mismatch', 'formatting_error',
        'text_overflow', 'cultural_inappropriateness', 'tone_mismatch',
        'gender_form_missing', 'plural_form_missing', 'technical_term_inconsistency',
        'audio_subtitle_mismatch', 'timing_sync_issue'
    )),
    
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    description TEXT NOT NULL,
    
    -- Context
    scene_id VARCHAR(128),
    line_id VARCHAR(128),
    speaker_id VARCHAR(128),
    screenshot_url TEXT,
    
    -- Resolution tracking
    status VARCHAR(32) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'wont_fix', 'deferred')),
    assigned_to VARCHAR(128),
    resolved_by VARCHAR(128),
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    
    -- Automated detection metadata
    detected_by VARCHAR(64), -- e.g., 'ui_snapshot_test', 'ai_player', 'manual_qa'
    confidence_score FLOAT CHECK (confidence_score BETWEEN 0 AND 1),
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_issues_key (key),
    INDEX idx_issues_language (language_code),
    INDEX idx_issues_build (build_id),
    INDEX idx_issues_type (issue_type),
    INDEX idx_issues_status (status),
    INDEX idx_issues_severity (severity)
);

-- Translation memory table (for consistency and reuse)
CREATE TABLE IF NOT EXISTS translation_memory (
    memory_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_text TEXT NOT NULL,
    source_language VARCHAR(10) NOT NULL DEFAULT 'en-US',
    target_text TEXT NOT NULL,
    target_language VARCHAR(10) NOT NULL,
    
    -- Usage context
    context_category VARCHAR(64),
    usage_count INTEGER NOT NULL DEFAULT 1,
    last_used_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Quality
    quality_score FLOAT CHECK (quality_score BETWEEN 0 AND 1),
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    verified_by VARCHAR(128),
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint to prevent duplicates
    UNIQUE(source_text, source_language, target_text, target_language),
    
    INDEX idx_tm_source (source_text),
    INDEX idx_tm_target_lang (target_language),
    INDEX idx_tm_quality (quality_score),
    INDEX idx_tm_usage (usage_count)
);

-- Supported languages configuration
CREATE TABLE IF NOT EXISTS supported_languages (
    language_code VARCHAR(10) PRIMARY KEY,
    language_name VARCHAR(64) NOT NULL,
    native_name VARCHAR(64) NOT NULL,
    
    -- Tier classification
    tier INTEGER NOT NULL CHECK (tier IN (1, 2, 3)), -- Tier 1: Full support, Tier 2: Subtitles only, Tier 3: UI only
    
    -- Feature support
    ui_support BOOLEAN NOT NULL DEFAULT TRUE,
    subtitle_support BOOLEAN NOT NULL DEFAULT FALSE,
    voice_support BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Language properties
    text_direction VARCHAR(10) NOT NULL DEFAULT 'ltr' CHECK (text_direction IN ('ltr', 'rtl')),
    requires_special_font BOOLEAN NOT NULL DEFAULT FALSE,
    font_family VARCHAR(128),
    
    -- Status
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    release_date DATE,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial supported languages
INSERT INTO supported_languages (language_code, language_name, native_name, tier, ui_support, subtitle_support, voice_support) VALUES
('en-US', 'English (US)', 'English', 1, TRUE, TRUE, TRUE),
('ja-JP', 'Japanese', '日本語', 1, TRUE, TRUE, TRUE),
('zh-CN', 'Chinese (Simplified)', '简体中文', 1, TRUE, TRUE, FALSE),
('ko-KR', 'Korean', '한국어', 2, TRUE, TRUE, FALSE),
('fr-FR', 'French', 'Français', 2, TRUE, TRUE, FALSE),
('de-DE', 'German', 'Deutsch', 2, TRUE, TRUE, FALSE),
('es-ES', 'Spanish', 'Español', 2, TRUE, TRUE, FALSE),
('pt-BR', 'Portuguese (Brazil)', 'Português', 2, TRUE, TRUE, FALSE),
('ru-RU', 'Russian', 'Русский', 3, TRUE, FALSE, FALSE),
('ar-SA', 'Arabic', 'العربية', 3, TRUE, FALSE, FALSE)
ON CONFLICT (language_code) DO NOTHING;

-- Functions for validation
CREATE OR REPLACE FUNCTION validate_localization_placeholders(text TEXT, reference_text TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    text_placeholders TEXT[];
    ref_placeholders TEXT[];
BEGIN
    -- Extract placeholders like %s, %d, %1$s, {{name}}, etc.
    text_placeholders := ARRAY(
        SELECT DISTINCT unnest(
            regexp_matches(text, '%[0-9]*\$?[sdif]|{{[^}]+}}|\{[0-9]+\}', 'g')
        )
    );
    
    ref_placeholders := ARRAY(
        SELECT DISTINCT unnest(
            regexp_matches(reference_text, '%[0-9]*\$?[sdif]|{{[^}]+}}|\{[0-9]+\}', 'g')
        )
    );
    
    -- Check if placeholders match
    RETURN text_placeholders::text[] = ref_placeholders::text[];
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Trigger to update timestamps
CREATE OR REPLACE FUNCTION update_localization_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_localization_entries_timestamp
    BEFORE UPDATE ON localization_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_localization_timestamp();

CREATE TRIGGER update_language_preferences_timestamp
    BEFORE UPDATE ON language_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_localization_timestamp();

-- Comments for clarity
COMMENT ON TABLE localization_entries IS 'Core localization strings for all game text. Supports pluralization, gendering, and version control.';
COMMENT ON TABLE language_preferences IS 'Per-player language settings including UI, subtitle, and voice preferences.';
COMMENT ON TABLE localization_coverage IS 'Build-specific metrics tracking translation completeness and quality per language/category.';
COMMENT ON TABLE localization_issues IS 'Quality issues found during localization QA, both automated and manual.';
COMMENT ON TABLE translation_memory IS 'Reusable translations for consistency across similar strings.';
COMMENT ON TABLE supported_languages IS 'Configuration of available languages and their feature support levels.';

COMMENT ON FUNCTION validate_localization_placeholders IS 'Validates that translated text contains the same placeholders as the reference text.';
