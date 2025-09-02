-- Migration: Rename columns in embeddings table
-- This migration renames text_embedding to embedding and original_text to content

-- Rename the columns
ALTER TABLE embeddings RENAME COLUMN text_embedding TO embedding;
ALTER TABLE embeddings RENAME COLUMN original_text TO content;

-- Update the match_embeddings function to use the new column names
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

-- Update the column comments
COMMENT ON COLUMN embeddings.embedding IS 'Primary embedding vector for similarity search (OpenAI text-embedding-3-small)';
COMMENT ON COLUMN embeddings.content IS 'Original text content of the document chunk';
