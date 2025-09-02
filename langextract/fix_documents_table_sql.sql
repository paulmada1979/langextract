-- Fix documents table structure
-- Run this in your Supabase SQL Editor

-- First, let's check the current structure
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'documents' 
ORDER BY ordinal_position;

-- Add any missing columns to documents table
ALTER TABLE documents ADD COLUMN IF NOT EXISTS filename VARCHAR(500);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS original_filename VARCHAR(500);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_type VARCHAR(50);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_size BIGINT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_path TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS upload_status VARCHAR(50) DEFAULT 'uploaded';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS processing_status VARCHAR(50) DEFAULT 'pending';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS processing_error TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename);
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
CREATE INDEX IF NOT EXISTS idx_documents_upload_status ON documents(upload_status);
CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN (metadata);

-- Add comments for documentation
COMMENT ON TABLE documents IS 'Table for tracking uploaded documents and their processing status';
COMMENT ON COLUMN documents.file_path IS 'Path to the stored file in the file system or cloud storage';
COMMENT ON COLUMN documents.upload_status IS 'Status of file upload: uploaded, processing, completed, failed';
COMMENT ON COLUMN documents.processing_status IS 'Status of document processing: pending, processing, completed, failed';

-- Verify the final structure
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'documents' 
ORDER BY ordinal_position;
