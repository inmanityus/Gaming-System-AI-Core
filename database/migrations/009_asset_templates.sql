-- Asset Templates and Cross-World Consistency System
-- Migration: 009_asset_templates.sql
-- Date: 2025-01-29

-- Asset templates for canonical asset definitions
CREATE TABLE IF NOT EXISTS asset_templates (
    template_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_type VARCHAR(100) NOT NULL,  -- 'building', 'landscape', 'interior', etc.
    asset_name VARCHAR(255) NOT NULL,
    canonical_description TEXT NOT NULL,  -- Minimal description for consistent generation
    ldt_specs JSONB DEFAULT '{}',  -- Light-Dark-Texture specifications
    generation_parameters JSONB DEFAULT '{}',  -- Parameters for model generation (seed, etc.)
    template_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA256 hash for consistency verification
    model_id UUID REFERENCES models(model_id),  -- Optional model ID for generation
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(asset_name, asset_type)
);

-- Asset generations tracking
CREATE TABLE IF NOT EXISTS asset_generations (
    generation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID REFERENCES asset_templates(template_id) ON DELETE CASCADE,
    world_id UUID NOT NULL,  -- World where asset was generated
    world_type VARCHAR(20) NOT NULL,  -- 'day' or 'dark'
    generation_prompt TEXT NOT NULL,  -- Prompt used for generation
    ldt_specs JSONB DEFAULT '{}',  -- Light-Dark-Texture specs used
    modifications JSONB DEFAULT '{}',  -- Story teller modifications (destruction, creation, etc.)
    template_hash VARCHAR(64) NOT NULL,  -- Hash of template used (for consistency check)
    generated_asset_path TEXT,  -- Path to generated asset (if stored)
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(template_id, world_id)  -- One generation per template per world
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_asset_templates_type ON asset_templates(asset_type);
CREATE INDEX IF NOT EXISTS idx_asset_templates_name ON asset_templates(asset_name);
CREATE INDEX IF NOT EXISTS idx_asset_templates_hash ON asset_templates(template_hash);
CREATE INDEX IF NOT EXISTS idx_asset_generations_template ON asset_generations(template_id);
CREATE INDEX IF NOT EXISTS idx_asset_generations_world ON asset_generations(world_id);
CREATE INDEX IF NOT EXISTS idx_asset_generations_template_world ON asset_generations(template_id, world_id);

