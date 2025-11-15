-- The Body Broker - World Events Table
-- Migration: 008_world_events
-- Created: 2025-01-29
-- Description: Adds the world_events table for dynamic world event management

-- ============================================================================
-- WORLD EVENTS TABLE
-- ============================================================================
CREATE TABLE world_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    trigger VARCHAR(100) NOT NULL,
    intensity NUMERIC(3, 2) NOT NULL CHECK (intensity >= 0 AND intensity <= 1),
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    duration INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    impact JSONB NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for world_events
CREATE INDEX idx_world_events_event_type ON world_events(event_type);
CREATE INDEX idx_world_events_status ON world_events(status);
CREATE INDEX idx_world_events_start_time ON world_events(start_time);
CREATE INDEX idx_world_events_end_time ON world_events(end_time);
CREATE INDEX idx_world_events_created_at ON world_events(created_at);
CREATE INDEX idx_world_events_impact ON world_events USING GIN(impact);
CREATE INDEX idx_world_events_metadata ON world_events USING GIN(metadata);

-- Comments for world_events table
COMMENT ON TABLE world_events IS 'Stores dynamic world events for simulation and narrative generation';
COMMENT ON COLUMN world_events.event_type IS 'Type of event (economic, political, social, natural, technological)';
COMMENT ON COLUMN world_events.trigger IS 'Trigger that caused this event';
COMMENT ON COLUMN world_events.intensity IS 'Event intensity from 0.0 to 1.0';
COMMENT ON COLUMN world_events.status IS 'Event status (pending, active, completed, cancelled)';
COMMENT ON COLUMN world_events.duration IS 'Event duration in seconds';
COMMENT ON COLUMN world_events.impact IS 'JSONB impact data on various systems';
COMMENT ON COLUMN world_events.metadata IS 'Additional event metadata';











