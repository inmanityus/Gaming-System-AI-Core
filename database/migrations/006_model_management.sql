-- Model Management System Database Schema
-- Migration: 006_model_management.sql
-- Date: 2025-01-29

-- Model registry
CREATE TABLE IF NOT EXISTS models (
    model_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(255) NOT NULL,
    model_type VARCHAR(50) NOT NULL,  -- 'paid' or 'self_hosted'
    provider VARCHAR(100),  -- 'openai', 'anthropic', 'huggingface', 'ollama', etc.
    use_case VARCHAR(100) NOT NULL,  -- 'story_generation', 'npc_dialogue', 'faction_decision', etc.
    version VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'candidate',  -- 'current', 'candidate', 'deprecated', 'testing'
    model_path TEXT,  -- Path to model files (self-hosted)
    configuration JSONB DEFAULT '{}',
    performance_metrics JSONB DEFAULT '{}',
    resource_requirements JSONB DEFAULT '{}',  -- VRAM, compute, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(model_name, version, use_case)
);

-- Historical logs for fine-tuning
CREATE TABLE IF NOT EXISTS model_historical_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES models(model_id) ON DELETE CASCADE,
    use_case VARCHAR(100),
    prompt TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    generated_output TEXT NOT NULL,
    user_feedback JSONB,  -- If user provided feedback/corrections
    corrected_output TEXT,  -- Corrected output if feedback provided
    performance_metrics JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Model snapshots for rollback
CREATE TABLE IF NOT EXISTS model_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES models(model_id) ON DELETE CASCADE,
    snapshot_name VARCHAR(255),
    model_state_path TEXT NOT NULL,  -- Path to saved model state
    configuration JSONB NOT NULL,
    performance_metrics JSONB DEFAULT '{}',
    traffic_allocation JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Guardrails violations
CREATE TABLE IF NOT EXISTS guardrails_violations (
    violation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES models(model_id) ON DELETE CASCADE,
    violation_type VARCHAR(50),  -- 'safety', 'addiction', 'harmful_content', etc.
    severity VARCHAR(20),  -- 'critical', 'high', 'medium', 'low'
    violation_details JSONB DEFAULT '{}',
    output_sample TEXT,
    intervention_taken VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Model deployment history
CREATE TABLE IF NOT EXISTS model_deployments (
    deployment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES models(model_id) ON DELETE CASCADE,
    deployment_type VARCHAR(50),  -- 'blue_green', 'canary', 'all_at_once'
    status VARCHAR(20) DEFAULT 'in_progress',  -- 'in_progress', 'completed', 'rolled_back', 'failed'
    traffic_percentage INTEGER DEFAULT 0,
    start_time TIMESTAMP DEFAULT NOW(),
    completion_time TIMESTAMP,
    rollback_reason TEXT
);

-- Fine-tuning jobs
CREATE TABLE IF NOT EXISTS fine_tuning_jobs (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES models(model_id) ON DELETE CASCADE,
    base_model_id UUID REFERENCES models(model_id),
    use_case VARCHAR(100) NOT NULL,
    training_data_source JSONB DEFAULT '{}',  -- Historical logs range, initial data sources
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'training', 'completed', 'failed'
    training_configuration JSONB DEFAULT '{}',
    training_metrics JSONB DEFAULT '{}',
    fine_tuned_model_path TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Model test results
CREATE TABLE IF NOT EXISTS model_test_results (
    test_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_model_id UUID REFERENCES models(model_id) ON DELETE CASCADE,
    current_model_id UUID REFERENCES models(model_id),
    test_type VARCHAR(50),  -- 'behavior_similarity', 'performance', 'safety', 'use_case'
    similarity_score FLOAT,
    performance_score FLOAT,
    safety_passed BOOLEAN,
    test_details JSONB DEFAULT '{}',
    meets_threshold BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_models_use_case_status ON models(use_case, status);
CREATE INDEX IF NOT EXISTS idx_models_type_status ON models(model_type, status);
CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider);
CREATE INDEX IF NOT EXISTS idx_historical_logs_model_time ON model_historical_logs(model_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_historical_logs_use_case ON model_historical_logs(use_case);
CREATE INDEX IF NOT EXISTS idx_guardrails_violations_model_time ON guardrails_violations(model_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_guardrails_violations_severity ON guardrails_violations(severity);
CREATE INDEX IF NOT EXISTS idx_model_snapshots_model_time ON model_snapshots(model_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_model_deployments_model_status ON model_deployments(model_id, status);
CREATE INDEX IF NOT EXISTS idx_fine_tuning_jobs_status ON fine_tuning_jobs(status);
CREATE INDEX IF NOT EXISTS idx_model_test_results_candidate ON model_test_results(candidate_model_id);








