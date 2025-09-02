-- MANUAL RESET: Embeddings Feature
-- Copy and paste this entire script into your Supabase SQL Editor

-- ==============================================
-- STEP 1: CLEANUP - Remove all embeddings-related objects
-- ==============================================

-- Drop the match_embeddings function
DROP FUNCTION IF EXISTS match_embeddings(vector(1536), float, integer);
DROP FUNCTION IF EXISTS match_embeddings(vector, double precision, integer);

-- Drop only the embeddings trigger (keep the shared function)
DROP TRIGGER IF EXISTS update_embeddings_updated_at ON embeddings;

-- Drop the embeddings table (this will also drop all indexes)
DROP TABLE IF EXISTS embeddings CASCADE;

-- ==============================================
-- STEP 2: RE-INITIALIZATION - Create fresh embeddings table
-- ==============================================

-- Enable the pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the embeddings table with correct column names
CREATE TABLE embeddings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    chunk_id VARCHAR(255) NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI text-embedding-3-small dimension
    all_embeddings JSONB, -- Store all embeddings (text, schemas, key_phrases)
    extracted_data JSONB, -- Store extracted structured data
    metadata JSONB, -- Store processing metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX idx_embeddings_document_id ON embeddings(document_id);
CREATE INDEX idx_embeddings_created_at ON embeddings(created_at);

-- Create a GIN index for JSONB fields
CREATE INDEX idx_embeddings_extracted_data ON embeddings USING GIN (extracted_data);
CREATE INDEX idx_embeddings_metadata ON embeddings USING GIN (metadata);

-- ==============================================
-- STEP 3: CREATE FUNCTIONS
-- ==============================================

-- Create the match_embeddings function
CREATE OR REPLACE FUNCTION match_embeddings(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    chunk_id VARCHAR(255),
    document_id VARCHAR(255),
    content TEXT,
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
        e.content,
        1 - (e.embedding <=> query_embedding) as similarity
    FROM embeddings e
    WHERE 1 - (e.embedding <=> query_embedding) > match_threshold
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create the match_documents function (alias for compatibility)
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    chunk_id VARCHAR(255),
    document_id VARCHAR(255),
    content TEXT,
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
        e.content,
        1 - (e.embedding <=> query_embedding) as similarity
    FROM embeddings e
    WHERE 1 - (e.embedding <=> query_embedding) > match_threshold
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create function to update the updated_at timestamp (only if it doesn't exist)
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

-- ==============================================
-- STEP 4: ADD COMMENTS FOR DOCUMENTATION
-- ==============================================

COMMENT ON TABLE embeddings IS 'Table for storing document embeddings with vector similarity search support';
COMMENT ON COLUMN embeddings.embedding IS 'Primary embedding vector for similarity search (OpenAI text-embedding-3-small)';
COMMENT ON COLUMN embeddings.content IS 'Original text content of the document chunk';
COMMENT ON COLUMN embeddings.all_embeddings IS 'JSON containing all generated embeddings (text, schemas, key_phrases)';
COMMENT ON COLUMN embeddings.extracted_data IS 'JSON containing extracted structured data from schemas';
COMMENT ON COLUMN embeddings.metadata IS 'JSON containing processing metadata and timestamps';

-- ==============================================
-- STEP 5: VERIFICATION QUERIES
-- ==============================================

-- Verify the table structure
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'embeddings' 
ORDER BY ordinal_position;

-- Verify the function exists
SELECT routine_name, routine_type 
FROM information_schema.routines 
WHERE routine_name = 'match_embeddings';

-- Test the function with a dummy vector
SELECT 'Function test successful' as status
WHERE EXISTS (
    SELECT 1 FROM match_embeddings(
        array_fill(0.1::real, ARRAY[1536])::vector(1536),
        0.5,
        1
    )
);

-- Show completion message
SELECT 'Embeddings feature reset completed successfully!' as message;
