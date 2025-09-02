-- Fix ambiguous user_id column reference in SQL function
-- Run this in your Supabase SQL Editor

-- Drop the existing function first
DROP FUNCTION IF EXISTS search_langextract_processed_embeddings(vector,uuid,uuid[],double precision,integer,character varying);

-- Create the search function with filter_user_id parameter instead of user_id
CREATE OR REPLACE FUNCTION search_langextract_processed_embeddings(
    query_embedding vector(1536),
    filter_user_id UUID DEFAULT NULL,
    document_ids UUID[] DEFAULT NULL,
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10,
    content_type_filter VARCHAR(50) DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    chunk_id VARCHAR(255),
    chunk_index INTEGER,
    content TEXT,
    content_type VARCHAR(50),
    extracted_metadata JSONB,
    chunk_metadata JSONB,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pe.id,
        pe.document_id,
        pe.chunk_id,
        pe.chunk_index,
        pe.content,
        pe.content_type,
        pe.extracted_metadata,
        pe.chunk_metadata,
        1 - (pe.embedding <=> query_embedding) as similarity
    FROM langextract_processed_embeddings pe
    WHERE 
        (filter_user_id IS NULL OR pe.user_id = filter_user_id)
        AND (document_ids IS NULL OR pe.document_id = ANY(document_ids))
        AND (content_type_filter IS NULL OR pe.content_type = content_type_filter)
        AND 1 - (pe.embedding <=> query_embedding) > match_threshold
    ORDER BY pe.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Verify the function was updated
SELECT routine_name, routine_definition 
FROM information_schema.routines 
WHERE routine_name = 'search_langextract_processed_embeddings';
