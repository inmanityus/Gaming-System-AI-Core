-- Aethelred Database Schema
-- AI Management System for Autonomous Development
-- Stores ARPs (Autonomous Resolution Packets) and Agent State

CREATE SCHEMA IF NOT EXISTS aethelred;

-- ARPs (Autonomous Resolution Packets) - Replaces Jira for AI-to-AI
CREATE TABLE IF NOT EXISTS aethelred.arps (
    arp_id VARCHAR(50) PRIMARY KEY,
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(50) NOT NULL,
    priority_score INTEGER NOT NULL,
    
    -- Detection
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    source_reports JSONB NOT NULL,
    consensus_analysis TEXT,
    
    -- Diagnosis
    root_cause_hypothesis TEXT,
    affected_systems TEXT[],
    likely_files TEXT[],
    
    -- Assignment
    assigned_to VARCHAR(100), -- Agent ID
    assigned_at TIMESTAMP WITH TIME ZONE,
    reviewers TEXT[],
    
    -- Development
    solution_plan TEXT,
    code_iterations JSONB,
    final_patch TEXT,
    
    -- Expert Oversight
    janus_vetting JSONB,
    janus_final_review JSONB,
    
    -- Testing
    regression_tests JSONB,
    
    -- Deployment
    deployment_history JSONB,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_arps_status (status),
    INDEX idx_arps_priority (priority_score DESC),
    INDEX idx_arps_assigned_to (assigned_to),
    INDEX idx_arps_created (created_at DESC)
);

-- AI Agents (Development Swarm members)
CREATE TABLE IF NOT EXISTS aethelred.agents (
    agent_id VARCHAR(100) PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL, -- 'coder', 'reviewer', 'analyzer', 'diagnostician'
    status VARCHAR(50) NOT NULL DEFAULT 'available',
    expertise_scores JSONB NOT NULL DEFAULT '{}',
    current_arp VARCHAR(50) REFERENCES aethelred.arps(arp_id),
    total_tasks_completed INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 1.0,
    average_completion_time_hours FLOAT DEFAULT 0.0,
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    INDEX idx_agents_status (status),
    INDEX idx_agents_role (role),
    INDEX idx_agents_model (model_name)
);

-- Agent Performance History
CREATE TABLE IF NOT EXISTS aethelred.agent_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(100) REFERENCES aethelred.agents(agent_id) NOT NULL,
    arp_id VARCHAR(50) REFERENCES aethelred.arps(arp_id) NOT NULL,
    role_in_arp VARCHAR(50) NOT NULL, -- 'lead_coder', 'reviewer'
    success BOOLEAN NOT NULL,
    completion_time_hours FLOAT,
    issues_found INTEGER DEFAULT 0, -- For reviewers
    code_quality_score FLOAT, -- From Janus
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    INDEX idx_performance_agent (agent_id),
    INDEX idx_performance_success (success)
);

-- ARP Events Log (Complete audit trail)
CREATE TABLE IF NOT EXISTS aethelred.arp_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    arp_id VARCHAR(50) REFERENCES aethelred.arps(arp_id) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    agent_id VARCHAR(100),
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    INDEX idx_events_arp (arp_id),
    INDEX idx_events_time (created_at DESC)
);

-- System Metrics (Daily rollup)
CREATE TABLE IF NOT EXISTS aethelred.daily_metrics (
    metric_date DATE PRIMARY KEY,
    arps_created INTEGER DEFAULT 0,
    arps_resolved INTEGER DEFAULT 0,
    arps_failed INTEGER DEFAULT 0,
    average_resolution_hours FLOAT,
    overall_success_rate FLOAT,
    model_api_cost_usd NUMERIC(10,2),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Grant permissions
GRANT ALL ON SCHEMA aethelred TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA aethelred TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA aethelred TO postgres;

