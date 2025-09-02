-- Migration: Create document processing tables for new API module
-- This migration creates tables for document upload, processing, and AI chat functionality

-- Enable the pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create documents table to track uploaded documents
CREATE TABLE IF NOT EXISTS documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL, -- pdf, docx, doc, md, txt
    file_size BIGINT NOT NULL,
    file_path TEXT NOT NULL, -- Path to stored file
    upload_status VARCHAR(50) DEFAULT 'uploaded', -- uploaded, processing, completed, failed
    processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    processing_error TEXT, -- Error message if processing failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}' -- Store file metadata like page count, etc.
);

-- Create processed_embeddings table for storing document chunks with embeddings
CREATE TABLE IF NOT EXISTS processed_embeddings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id VARCHAR(255) NOT NULL,
    chunk_index INTEGER NOT NULL, -- Order of chunk in document
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text', -- text, table, image, etc.
    embedding vector(1536), -- OpenAI text-embedding-3-small dimension
    all_embeddings JSONB, -- Store all embeddings (text, schemas, key_phrases)
    extracted_metadata JSONB, -- Store extracted structured data from langextract
    chunk_metadata JSONB, -- Store chunk-specific metadata (page, position, etc.)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create chat_sessions table for AI chat functionality
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_name VARCHAR(255) DEFAULT 'New Chat',
    document_ids UUID[] DEFAULT '{}', -- Array of document IDs this chat can access
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create chat_messages table for storing chat history
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}', -- Store message metadata (tokens, model, etc.)
    referenced_chunks UUID[] DEFAULT '{}', -- Array of chunk IDs referenced in response
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
-- Documents table indexes
CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename);
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
CREATE INDEX IF NOT EXISTS idx_documents_upload_status ON documents(upload_status);
CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);

-- Processed embeddings table indexes
CREATE INDEX IF NOT EXISTS idx_processed_embeddings_document_id ON processed_embeddings(document_id);
CREATE INDEX IF NOT EXISTS idx_processed_embeddings_chunk_id ON processed_embeddings(chunk_id);
CREATE INDEX IF NOT EXISTS idx_processed_embeddings_chunk_index ON processed_embeddings(chunk_index);
CREATE INDEX IF NOT EXISTS idx_processed_embeddings_content_type ON processed_embeddings(content_type);
CREATE INDEX IF NOT EXISTS idx_processed_embeddings_created_at ON processed_embeddings(created_at);

-- GIN indexes for JSONB fields
CREATE INDEX IF NOT EXISTS idx_processed_embeddings_extracted_metadata ON processed_embeddings USING GIN (extracted_metadata);
CREATE INDEX IF NOT EXISTS idx_processed_embeddings_chunk_metadata ON processed_embeddings USING GIN (chunk_metadata);
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN (metadata);

-- Chat tables indexes
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_last_activity ON chat_sessions(last_activity);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_message_type ON chat_messages(message_type);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);

-- Create a function for similarity search in processed_embeddings
CREATE OR REPLACE FUNCTION search_processed_embeddings(
    query_embedding vector(1536),
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
    FROM processed_embeddings pe
    WHERE 
        (document_ids IS NULL OR pe.document_id = ANY(document_ids))
        AND (content_type_filter IS NULL OR pe.content_type = content_type_filter)
        AND 1 - (pe.embedding <=> query_embedding) > match_threshold
    ORDER BY pe.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create a function to get document statistics
CREATE OR REPLACE FUNCTION get_document_stats(document_id UUID)
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
    FROM documents d
    LEFT JOIN processed_embeddings pe ON d.id = pe.document_id
    LEFT JOIN (
        SELECT content_type, COUNT(*) as type_count
        FROM processed_embeddings
        WHERE document_id = $1
        GROUP BY content_type
    ) type_stats ON pe.content_type = type_stats.content_type
    WHERE d.id = $1
    GROUP BY d.processing_status;
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

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_processed_embeddings_updated_at 
    BEFORE UPDATE ON processed_embeddings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_sessions_updated_at 
    BEFORE UPDATE ON chat_sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create a function to clean up old chat sessions (optional maintenance)
CREATE OR REPLACE FUNCTION cleanup_old_chat_sessions(days_old INTEGER DEFAULT 30)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM chat_sessions 
    WHERE last_activity < NOW() - INTERVAL '1 day' * days_old;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

-- Add comments for documentation
COMMENT ON TABLE documents IS 'Table for tracking uploaded documents and their processing status';
COMMENT ON TABLE processed_embeddings IS 'Table for storing document chunks with embeddings and extracted metadata';
COMMENT ON TABLE chat_sessions IS 'Table for managing AI chat sessions with documents';
COMMENT ON TABLE chat_messages IS 'Table for storing chat message history';

COMMENT ON COLUMN documents.file_path IS 'Path to the stored file in the file system or cloud storage';
COMMENT ON COLUMN documents.upload_status IS 'Status of file upload: uploaded, processing, completed, failed';
COMMENT ON COLUMN documents.processing_status IS 'Status of document processing: pending, processing, completed, failed';

COMMENT ON COLUMN processed_embeddings.chunk_index IS 'Order of this chunk within the document (0-based)';
COMMENT ON COLUMN processed_embeddings.content_type IS 'Type of content: text, table, image, header, etc.';
COMMENT ON COLUMN processed_embeddings.embedding IS 'Primary embedding vector for similarity search';
COMMENT ON COLUMN processed_embeddings.extracted_metadata IS 'Structured data extracted using langextract schemas';
COMMENT ON COLUMN processed_embeddings.chunk_metadata IS 'Chunk-specific metadata like page number, position, etc.';

COMMENT ON COLUMN chat_sessions.document_ids IS 'Array of document IDs that this chat session can access';
COMMENT ON COLUMN chat_messages.referenced_chunks IS 'Array of chunk IDs that were referenced in the AI response';
