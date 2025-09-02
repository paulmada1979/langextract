-- Migration: Add user_id columns to langextract tables for user isolation
-- This migration adds user_id UUID columns to all langextract tables

-- Add user_id column to langextract_documents table
ALTER TABLE langextract_documents ADD COLUMN IF NOT EXISTS user_id UUID;

-- Add user_id column to langextract_processed_embeddings table
ALTER TABLE langextract_processed_embeddings ADD COLUMN IF NOT EXISTS user_id UUID;

-- Add user_id column to langextract_chat_sessions table
ALTER TABLE langextract_chat_sessions ADD COLUMN IF NOT EXISTS user_id UUID;

-- Add user_id column to langextract_chat_messages table
ALTER TABLE langextract_chat_messages ADD COLUMN IF NOT EXISTS user_id UUID;

-- Create indexes for user_id columns for better performance
CREATE INDEX IF NOT EXISTS idx_langextract_documents_user_id ON langextract_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_langextract_processed_embeddings_user_id ON langextract_processed_embeddings(user_id);
CREATE INDEX IF NOT EXISTS idx_langextract_chat_sessions_user_id ON langextract_chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_langextract_chat_messages_user_id ON langextract_chat_messages(user_id);

-- Create composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_langextract_documents_user_created ON langextract_documents(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_langextract_processed_embeddings_user_document ON langextract_processed_embeddings(user_id, document_id);
CREATE INDEX IF NOT EXISTS idx_langextract_chat_sessions_user_activity ON langextract_chat_sessions(user_id, last_activity);
CREATE INDEX IF NOT EXISTS idx_langextract_chat_messages_user_session ON langextract_chat_messages(user_id, session_id);

-- Update the search function to include user_id filtering
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

-- Update the document stats function to include user_id filtering
CREATE OR REPLACE FUNCTION get_langextract_document_stats(document_id UUID, filter_user_id UUID DEFAULT NULL)
RETURNS TABLE (
    total_chunks INTEGER,
    total_content_length BIGINT,
    content_types JSONB,
    processing_status VARCHAR(50)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(pe.id)::INTEGER as total_chunks,
        SUM(LENGTH(pe.content))::BIGINT as total_content_length,
        jsonb_object_agg(pe.content_type, type_count) as content_types,
        d.processing_status
    FROM langextract_documents d
    LEFT JOIN langextract_processed_embeddings pe ON d.id = pe.document_id
    LEFT JOIN (
        SELECT content_type, COUNT(*) as type_count
        FROM langextract_processed_embeddings
        WHERE document_id = $1 AND (filter_user_id IS NULL OR user_id = filter_user_id)
        GROUP BY content_type
    ) type_stats ON pe.content_type = type_stats.content_type
    WHERE d.id = $1 AND (filter_user_id IS NULL OR d.user_id = filter_user_id)
    GROUP BY d.processing_status;
END;
$$;

-- Add comments for documentation
COMMENT ON COLUMN langextract_documents.user_id IS 'UUID of the user who uploaded this document';
COMMENT ON COLUMN langextract_processed_embeddings.user_id IS 'UUID of the user who owns this document chunk';
COMMENT ON COLUMN langextract_chat_sessions.user_id IS 'UUID of the user who owns this chat session';
COMMENT ON COLUMN langextract_chat_messages.user_id IS 'UUID of the user who owns this chat message';

-- Verify the columns were added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name LIKE 'langextract_%' 
AND column_name = 'user_id'
ORDER BY table_name;
