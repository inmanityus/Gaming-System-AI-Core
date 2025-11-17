-- Addiction Risk Reports Tables
-- For tracking cohort-level addiction risk indicators and reports

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table for storing cohort-level addiction risk reports
CREATE TABLE IF NOT EXISTS addiction_risk_reports (
    report_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    build_id VARCHAR(128) NOT NULL,
    report_date DATE NOT NULL,
    cohort_identifier JSONB NOT NULL, -- e.g., {"region": "NA", "age_band": "18-24", "platform": "PC"}
    
    -- Addiction risk indicators (R-EMO-ADD-001 to R-EMO-ADD-003)
    night_time_fraction FLOAT CHECK (night_time_fraction BETWEEN 0.0 AND 1.0), -- Fraction of play during unhealthy hours
    one_more_run_loops FLOAT CHECK (one_more_run_loops >= 0), -- Average "one more run" behavior per cohort
    excessive_session_fraction FLOAT CHECK (excessive_session_fraction BETWEEN 0.0 AND 1.0), -- Fraction of sessions > 4 hours
    avg_session_duration_hours FLOAT CHECK (avg_session_duration_hours >= 0),
    max_session_duration_hours FLOAT CHECK (max_session_duration_hours >= 0),
    
    -- Additional risk metrics
    consecutive_days_played_p90 INTEGER CHECK (consecutive_days_played_p90 >= 0), -- 90th percentile of consecutive days
    avg_time_between_sessions_hours FLOAT CHECK (avg_time_between_sessions_hours >= 0),
    early_morning_sessions_fraction FLOAT CHECK (early_morning_sessions_fraction BETWEEN 0.0 AND 1.0), -- 2am-6am
    weekend_vs_weekday_ratio FLOAT CHECK (weekend_vs_weekday_ratio >= 0),
    
    -- Engagement context (for correlation)
    avg_npc_attachment_index FLOAT CHECK (avg_npc_attachment_index BETWEEN 0.0 AND 1.0),
    avg_moral_tension_index FLOAT CHECK (avg_moral_tension_index BETWEEN 0.0 AND 1.0),
    dominant_engagement_profile VARCHAR(64), -- e.g., 'lore-focused', 'power-gamer', 'explorer'
    
    -- Analysis metadata
    sample_size INTEGER NOT NULL CHECK (sample_size > 0),
    confidence_level FLOAT CHECK (confidence_level BETWEEN 0.0 AND 1.0),
    risk_level VARCHAR(32) NOT NULL CHECK (risk_level IN ('healthy', 'moderate', 'concerning', 'severe')),
    risk_factors TEXT[], -- Array of identified risk factors
    recommendations TEXT[], -- Design recommendations for this cohort
    
    -- Associated systems/features with elevated indicators
    high_risk_features JSONB NOT NULL DEFAULT '[]'::jsonb, -- e.g., [{"feature": "endless_mode", "correlation": 0.73}]
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for efficient querying
    INDEX idx_addiction_reports_build (build_id),
    INDEX idx_addiction_reports_date (report_date),
    INDEX idx_addiction_reports_risk (risk_level),
    INDEX idx_addiction_reports_cohort ((cohort_identifier->>'region'), (cohort_identifier->>'age_band'), (cohort_identifier->>'platform'))
);

-- Table for tracking addiction risk thresholds and configuration
CREATE TABLE IF NOT EXISTS addiction_risk_thresholds (
    threshold_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(128) NOT NULL UNIQUE,
    healthy_max FLOAT,
    moderate_max FLOAT,
    concerning_max FLOAT,
    -- severe is anything above concerning_max
    description TEXT,
    unit VARCHAR(32),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(128)
);

-- Insert default thresholds (can be adjusted by ethics team)
INSERT INTO addiction_risk_thresholds (metric_name, healthy_max, moderate_max, concerning_max, description, unit) VALUES
('night_time_fraction', 0.15, 0.30, 0.50, 'Fraction of gameplay during unhealthy hours (11pm-5am)', 'fraction'),
('one_more_run_loops', 2.0, 4.0, 6.0, 'Average number of "one more run" loops per session', 'count'),
('excessive_session_fraction', 0.10, 0.25, 0.40, 'Fraction of sessions exceeding 4 hours', 'fraction'),
('avg_session_duration_hours', 2.0, 3.5, 5.0, 'Average session duration', 'hours'),
('consecutive_days_played_p90', 14, 21, 30, '90th percentile of consecutive days played', 'days'),
('early_morning_sessions_fraction', 0.05, 0.15, 0.30, 'Fraction of sessions starting between 2am-6am', 'fraction')
ON CONFLICT (metric_name) DO NOTHING;

