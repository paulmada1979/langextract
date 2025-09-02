#!/usr/bin/env python3
"""
Script to check and fix the documents table structure.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.supabase_client import supabase_client

def check_documents_table():
    """Check the current structure of the documents table."""
    
    if not supabase_client.is_available():
        print("❌ Supabase client not available")
        return False
    
    client = supabase_client.get_client()
    
    try:
        # Try to get the table structure by selecting from it
        result = client.table('documents').select('*').limit(1).execute()
        print("✅ Documents table exists and is accessible")
        
        # Check what columns exist by trying to insert a test record
        test_data = {
            'filename': 'test.txt',
            'original_filename': 'test.txt',
            'file_type': 'txt',
            'file_size': 100,
            'file_path': '/tmp/test.txt',
            'upload_status': 'uploaded',
            'processing_status': 'pending'
        }
        
        print("🔍 Checking required columns...")
        missing_columns = []
        
        # Test each column
        for column in ['filename', 'original_filename', 'file_type', 'file_size', 'file_path', 'upload_status', 'processing_status']:
            try:
                test_result = client.table('documents').insert({column: test_data[column]}).execute()
                print(f"   ✅ Column '{column}' exists")
            except Exception as e:
                if 'column' in str(e).lower() and 'does not exist' in str(e).lower():
                    print(f"   ❌ Column '{column}' is missing")
                    missing_columns.append(column)
                else:
                    print(f"   ✅ Column '{column}' exists (other error: {str(e)[:50]}...)")
        
        return missing_columns
        
    except Exception as e:
        print(f"❌ Error checking documents table: {e}")
        return None

def fix_documents_table():
    """Add missing columns to the documents table."""
    
    print("\n🔧 Adding missing columns to documents table...")
    print("Please run these SQL statements in your Supabase SQL Editor:")
    print("=" * 60)
    
    sql_statements = [
        "-- Add missing columns to documents table",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS filename VARCHAR(500);",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS original_filename VARCHAR(500);",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_type VARCHAR(50);",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_size BIGINT;",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_path TEXT;",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS upload_status VARCHAR(50) DEFAULT 'uploaded';",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS processing_status VARCHAR(50) DEFAULT 'pending';",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS processing_error TEXT;",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';",
        "",
        "-- Add indexes for better performance",
        "CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename);",
        "CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);",
        "CREATE INDEX IF NOT EXISTS idx_documents_upload_status ON documents(upload_status);",
        "CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents(processing_status);",
        "CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN (metadata);",
        "",
        "-- Add comments for documentation",
        "COMMENT ON TABLE documents IS 'Table for tracking uploaded documents and their processing status';",
        "COMMENT ON COLUMN documents.file_path IS 'Path to the stored file in the file system or cloud storage';",
        "COMMENT ON COLUMN documents.upload_status IS 'Status of file upload: uploaded, processing, completed, failed';",
        "COMMENT ON COLUMN documents.processing_status IS 'Status of document processing: pending, processing, completed, failed';"
    ]
    
    for statement in sql_statements:
        print(statement)
    
    print("=" * 60)
    print("Copy the above SQL statements and run them in your Supabase SQL Editor.")

if __name__ == "__main__":
    print("🚀 Documents Table Structure Checker")
    print("=" * 50)
    
    missing_columns = check_documents_table()
    
    if missing_columns is None:
        print("\n❌ Could not check table structure")
    elif missing_columns:
        print(f"\n⚠️  Found {len(missing_columns)} missing columns: {missing_columns}")
        fix_documents_table()
    else:
        print("\n✅ All required columns exist in the documents table!")
        print("The table structure looks correct.")
