-- Story Branches Table
-- Migration: 007_story_branches
-- Date: 2025-01-29

-- ============================================================================
-- STORY BRANCHES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS story_branches (
    branch_id VARCHAR(255) PRIMARY KEY,
    from_node_id UUID NOT NULL,
    to_node_id UUID NOT NULL,
    conditions JSONB NOT NULL DEFAULT '{}',
    weight NUMERIC(4, 2) NOT NULL DEFAULT 1.0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_story_branches_from FOREIGN KEY (from_node_id) REFERENCES story_nodes(id) ON DELETE CASCADE,
    CONSTRAINT fk_story_branches_to FOREIGN KEY (to_node_id) REFERENCES story_nodes(id) ON DELETE CASCADE
);

-- Indexes for story_branches
CREATE INDEX IF NOT EXISTS idx_story_branches_from_node_id ON story_branches(from_node_id);
CREATE INDEX IF NOT EXISTS idx_story_branches_to_node_id ON story_branches(to_node_id);
CREATE INDEX IF NOT EXISTS idx_story_branches_is_active ON story_branches(is_active);
CREATE INDEX IF NOT EXISTS idx_story_branches_conditions ON story_branches USING GIN(conditions);



