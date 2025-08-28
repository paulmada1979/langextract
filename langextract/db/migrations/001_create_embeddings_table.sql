-- Migration: Create embeddings table with vector support
-- This migration creates a table for storing document embeddings with pgvector support

-- Enable the pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the embeddings table
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    chunk_id VARCHAR(255) NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    original_text TEXT NOT NULL,
    text_embedding vector(1536), -- OpenAI text-embedding-3-small dimension
    all_embeddings JSONB, -- Store all embeddings (text, schemas, key_phrases)
    extracted_data JSONB, -- Store extracted structured data
    metadata JSONB, -- Store processing metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_document_id ON embeddings(document_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_created_at ON embeddings(created_at);

-- Create a GIN index for JSONB fields
CREATE INDEX IF NOT EXISTS idx_embeddings_extracted_data ON embeddings USING GIN (extracted_data);
CREATE INDEX IF NOT EXISTS idx_embeddings_metadata ON embeddings USING GIN (metadata);

-- Create a function for similarity search using cosine distance
CREATE OR REPLACE FUNCTION match_embeddings(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    chunk_id VARCHAR(255),
    document_id VARCHAR(255),
    original_text TEXT,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        e.chunk_id,
        e.document_id,
        e.original_text,
        1 - (e.text_embedding <=> query_embedding) as similarity
    FROM embeddings e
    WHERE 1 - (e.text_embedding <=> query_embedding) > match_threshold
    ORDER BY e.text_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_embeddings_updated_at 
    BEFORE UPDATE ON embeddings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE embeddings IS 'Table for storing document embeddings with vector similarity search support';
COMMENT ON COLUMN embeddings.text_embedding IS 'Primary embedding vector for similarity search (OpenAI text-embedding-3-small)';
COMMENT ON COLUMN embeddings.all_embeddings IS 'JSON containing all generated embeddings (text, schemas, key_phrases)';
COMMENT ON COLUMN embeddings.extracted_data IS 'JSON containing extracted structured data from schemas';
COMMENT ON COLUMN embeddings.metadata IS 'JSON containing processing metadata and timestamps';

