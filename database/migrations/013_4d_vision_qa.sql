-- 4D Vision QA System Tables
-- For storing segments, issues, summaries, and coverage metrics

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 4D capture segments
CREATE TABLE IF NOT EXISTS vision_segments (
    segment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    build_id VARCHAR(128) NOT NULL,
    scene_id VARCHAR(128) NOT NULL,
    level_name VARCHAR(128) NOT NULL,
    test_scenario VARCHAR(256),
    
    -- Timing
    start_timestamp TIMESTAMP NOT NULL,
    end_timestamp TIMESTAMP NOT NULL,
    duration_seconds FLOAT NOT NULL,
    frame_count INTEGER NOT NULL,
    
    -- Capture configuration
    sampling_mode VARCHAR(32) NOT NULL CHECK (sampling_mode IN ('frame_level', 'window_based', 'event_based')),
    camera_configs JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of camera configurations
    
    -- Media references
    media_uris JSONB NOT NULL DEFAULT '{}'::jsonb, -- camera_id -> storage URI mapping
    depth_uris JSONB NOT NULL DEFAULT '{}'::jsonb, -- camera_id -> depth URI mapping
    
    -- Performance metrics
    performance_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Gameplay events
    gameplay_events JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    -- Analysis status
    analysis_status VARCHAR(32) NOT NULL DEFAULT 'pending' CHECK (analysis_status IN ('pending', 'analyzing', 'completed', 'failed')),
    analyzed_at TIMESTAMP,
    
    -- Metadata
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_segments_build (build_id),
    INDEX idx_segments_scene (scene_id),
    INDEX idx_segments_status (analysis_status),
    INDEX idx_segments_timestamp (start_timestamp)
);

-- 4D Vision issues/findings
CREATE TABLE IF NOT EXISTS vision_issues (
    issue_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    segment_id UUID NOT NULL REFERENCES vision_segments(segment_id) ON DELETE CASCADE,
    
    -- Detection info
    detector_type VARCHAR(32) NOT NULL CHECK (detector_type IN ('animation', 'physics', 'rendering', 'lighting', 'performance', 'flow')),
    issue_type VARCHAR(128) NOT NULL,
    
    -- Severity and confidence
    severity FLOAT NOT NULL CHECK (severity BETWEEN 0 AND 1),
    confidence FLOAT NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    
    -- Location in 4D space
    timestamp TIMESTAMP NOT NULL,
    camera_id VARCHAR(64),
    screen_coords FLOAT[],  -- normalized 0-1 coordinates
    world_coords FLOAT[],   -- game world coordinates
    
    -- Evidence and explanation
    description TEXT NOT NULL,
    evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb, -- URIs to specific frames
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb, -- Detector-specific measurements
    
    -- Impact assessment
    affected_goals TEXT[] DEFAULT '{}',  -- G-IMMERSION, G-HORROR, etc.
    player_impact FLOAT CHECK (player_impact BETWEEN 0 AND 1),
    
    -- Explainability (R-SYS-SAFE-004)
    explanation TEXT,
    threshold_details JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_issues_segment (segment_id),
    INDEX idx_issues_detector (detector_type),
    INDEX idx_issues_severity (severity),
    INDEX idx_issues_timestamp (timestamp)
);

-- Scene-level summaries
CREATE TABLE IF NOT EXISTS vision_scene_summaries (
    summary_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    build_id VARCHAR(128) NOT NULL,
    scene_id VARCHAR(128) NOT NULL,
    
    -- Aggregate metrics
    total_segments INTEGER NOT NULL DEFAULT 0,
    analyzed_segments INTEGER NOT NULL DEFAULT 0,
    
    -- Issue breakdown
    issue_counts JSONB NOT NULL DEFAULT '{}'::jsonb, -- detector_type -> count
    avg_severities JSONB NOT NULL DEFAULT '{}'::jsonb, -- detector_type -> avg severity
    
    -- Key findings
    critical_issues TEXT[] DEFAULT '{}',
    recurring_patterns TEXT[] DEFAULT '{}',
    
    -- Overall scores
    visual_quality_score FLOAT CHECK (visual_quality_score BETWEEN 0 AND 1),
    horror_atmosphere_score FLOAT CHECK (horror_atmosphere_score BETWEEN 0 AND 1),
    technical_stability_score FLOAT CHECK (technical_stability_score BETWEEN 0 AND 1),
    
    -- Timestamps
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE (build_id, scene_id),
    
    -- Indexes
    INDEX idx_summaries_build (build_id),
    INDEX idx_summaries_scene (scene_id)
);

-- Coverage reports
CREATE TABLE IF NOT EXISTS vision_coverage_reports (
    report_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    build_id VARCHAR(128) NOT NULL UNIQUE,
    
    -- Coverage metrics
    total_scenes INTEGER NOT NULL,
    analyzed_scenes INTEGER NOT NULL,
    coverage_percentage FLOAT NOT NULL CHECK (coverage_percentage BETWEEN 0 AND 100),
    
    -- Breakdown by scene type
    coverage_by_type JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Missing coverage
    unanalyzed_scenes TEXT[] DEFAULT '{}',
    partial_coverage_scenes TEXT[] DEFAULT '{}',
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_coverage_build (build_id)
);

-- Trend analysis
CREATE TABLE IF NOT EXISTS vision_trends (
    trend_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    build_id VARCHAR(128) NOT NULL,
    comparison_build_id VARCHAR(128) NOT NULL,
    
    -- Trend data
    trends JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of trend items
    regression_alerts TEXT[] DEFAULT '{}',
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_trends_build (build_id),
    INDEX idx_trends_comparison (comparison_build_id)
);

-- Analysis queue (for tracking processing)
CREATE TABLE IF NOT EXISTS vision_analysis_queue (
    queue_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    segment_id UUID NOT NULL REFERENCES vision_segments(segment_id) ON DELETE CASCADE,
    
    priority INTEGER NOT NULL DEFAULT 5, -- 1-10, higher is more urgent
    detector_types TEXT[] NOT NULL DEFAULT '{}',
    analysis_params JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Processing status
    status VARCHAR(32) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    attempts INTEGER NOT NULL DEFAULT 0,
    last_attempt_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_queue_status (status),
    INDEX idx_queue_priority (priority DESC)
);
