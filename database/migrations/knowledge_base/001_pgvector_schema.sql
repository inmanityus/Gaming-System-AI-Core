-- Knowledge Base Schema with pgvector
-- Creates tables for storyteller's persistent memory with semantic search

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- NARRATIVE DOCUMENTS TABLE
-- Stores chunked narrative documents with embeddings for semantic search
-- ============================================================================
CREATE TABLE narrative_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    source_file VARCHAR(500) NOT NULL,  -- Original file path
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,  -- For multi-chunk documents
    total_chunks INTEGER NOT NULL,
    document_type VARCHAR(50) NOT NULL,  -- 'main', 'guide', 'experience'
    embedding vector(1536),  -- OpenAI ada-002 or AWS Titan dimensions
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_document_chunk UNIQUE(source_file, chunk_index)
);

-- Indexes for narrative_documents
CREATE INDEX idx_narrative_documents_source ON narrative_documents(source_file);
CREATE INDEX idx_narrative_documents_type ON narrative_documents(document_type);
CREATE INDEX idx_narrative_documents_embedding ON narrative_documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================================
-- NARRATIVE CONCEPTS TABLE
-- Tracks key concepts (characters, factions, locations, rules) with embeddings
-- ============================================================================
CREATE TABLE narrative_concepts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    concept_type VARCHAR(50) NOT NULL,  -- 'character', 'faction', 'location', 'rule', 'event'
    description TEXT NOT NULL,
    scope VARCHAR(50) NOT NULL,  -- 'global', 'day_world', 'dark_world', 'experience'
    world_id UUID,  -- NULL for global concepts
    embedding vector(1536),
    source_documents UUID[],  -- References to narrative_documents
    relationships JSONB NOT NULL DEFAULT '{}',  -- Links to other concepts
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for narrative_concepts
CREATE INDEX idx_narrative_concepts_name ON narrative_concepts(name);
CREATE INDEX idx_narrative_concepts_type ON narrative_concepts(concept_type);
CREATE INDEX idx_narrative_concepts_scope ON narrative_concepts(scope);
CREATE INDEX idx_narrative_concepts_world ON narrative_concepts(world_id);
CREATE INDEX idx_narrative_concepts_embedding ON narrative_concepts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================================
-- CONCEPT VERSIONS TABLE
-- Tracks how concepts evolve over time (character growth, faction changes)
-- ============================================================================
CREATE TABLE concept_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    concept_id UUID NOT NULL REFERENCES narrative_concepts(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    description TEXT NOT NULL,
    changes JSONB NOT NULL DEFAULT '{}',  -- What changed from previous version
    world_id UUID,  -- Which world this version applies to
    player_id UUID,  -- If concept is player-specific
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_concept_version UNIQUE(concept_id, version_number, world_id, player_id)
);

-- Indexes for concept_versions
CREATE INDEX idx_concept_versions_concept ON concept_versions(concept_id);
CREATE INDEX idx_concept_versions_world ON concept_versions(world_id);
CREATE INDEX idx_concept_versions_player ON concept_versions(player_id);

-- ============================================================================
-- WORLDS TABLE
-- Player world instances (each player has their own world state)
-- ============================================================================
CREATE TABLE worlds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL,  -- Owner of this world
    world_type VARCHAR(50) NOT NULL,  -- 'day', 'dark', 'experience'
    world_name VARCHAR(255),
    world_state JSONB NOT NULL DEFAULT '{}',  -- Current state
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for worlds
CREATE INDEX idx_worlds_player ON worlds(player_id);
CREATE INDEX idx_worlds_type ON worlds(world_type);
CREATE INDEX idx_worlds_active ON worlds(active);

-- ============================================================================
-- STORY EVENTS TABLE
-- Tracks story events per world for persistent history
-- ============================================================================
CREATE TABLE story_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    world_id UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,  -- 'dialogue', 'choice', 'combat', 'discovery'
    event_data JSONB NOT NULL DEFAULT '{}',
    involved_npcs UUID[],  -- NPCs involved in event
    impact_score FLOAT DEFAULT 0.0,  -- How significant (0.0-1.0)
    embedding vector(1536),  -- For semantic similarity search
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for story_events
CREATE INDEX idx_story_events_world ON story_events(world_id);
CREATE INDEX idx_story_events_type ON story_events(event_type);
CREATE INDEX idx_story_events_impact ON story_events(impact_score);
CREATE INDEX idx_story_events_embedding ON story_events USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_story_events_created ON story_events(created_at DESC);

-- ============================================================================
-- CONCEPT RELATIONSHIPS TABLE
-- Lightweight graph of relationships between concepts
-- ============================================================================
CREATE TABLE concept_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    concept_a_id UUID NOT NULL REFERENCES narrative_concepts(id) ON DELETE CASCADE,
    concept_b_id UUID NOT NULL REFERENCES narrative_concepts(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,  -- 'allied_with', 'enemy_of', 'member_of', 'located_in'
    strength FLOAT DEFAULT 0.5,  -- 0.0-1.0
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_relationship UNIQUE(concept_a_id, concept_b_id, relationship_type)
);

-- Indexes for concept_relationships
CREATE INDEX idx_concept_relationships_a ON concept_relationships(concept_a_id);
CREATE INDEX idx_concept_relationships_b ON concept_relationships(concept_b_id);
CREATE INDEX idx_concept_relationships_type ON concept_relationships(relationship_type);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Global knowledge accessible to all storytellers
CREATE VIEW global_knowledge AS
SELECT 
    id, name, concept_type, description, scope, embedding
FROM narrative_concepts
WHERE scope = 'global';

-- Per-world knowledge (global + world-specific)
CREATE OR REPLACE FUNCTION get_world_knowledge(p_world_id UUID)
RETURNS TABLE(
    id UUID,
    name VARCHAR(255),
    concept_type VARCHAR(50),
    description TEXT,
    scope VARCHAR(50),
    embedding vector(1536)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        nc.id, nc.name, nc.concept_type, nc.description, nc.scope, nc.embedding
    FROM narrative_concepts nc
    WHERE nc.scope = 'global' OR nc.world_id = p_world_id;
END;
$$ LANGUAGE plpgsql;

-- Semantic search function
CREATE OR REPLACE FUNCTION semantic_search_documents(
    query_embedding vector(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INTEGER DEFAULT 10
)
RETURNS TABLE(
    id UUID,
    title VARCHAR(255),
    content TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        nd.id,
        nd.title,
        nd.content,
        1 - (nd.embedding <=> query_embedding) AS similarity
    FROM narrative_documents nd
    WHERE 1 - (nd.embedding <=> query_embedding) > match_threshold
    ORDER BY nd.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Knowledge Base schema created successfully with pgvector support';
END $$;

