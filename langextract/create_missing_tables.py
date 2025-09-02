#!/usr/bin/env python3
"""
Script to create the missing processed_embeddings table and other required tables.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.supabase_client import supabase_client

def create_missing_tables():
    """Create the missing tables."""
    
    if not supabase_client.is_available():
        print("❌ Supabase client not available. Please check your environment variables:")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_ANON_KEY")
        return False
    
    client = supabase_client.get_client()
    
    # SQL statements to create the missing tables
    sql_statements = [
        # Enable pgvector extension
        "CREATE EXTENSION IF NOT EXISTS vector;",
        
        # Create processed_embeddings table
        """CREATE TABLE IF NOT EXISTS processed_embeddings (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_id VARCHAR(255) NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            content_type VARCHAR(50) DEFAULT 'text',
            embedding vector(1536),
            all_embeddings JSONB,
            extracted_metadata JSONB,
            chunk_metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );""",
        
        # Create chat_sessions table
        """CREATE TABLE IF NOT EXISTS chat_sessions (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            session_name VARCHAR(255) DEFAULT 'New Chat',
            document_ids UUID[] DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );""",
        
        # Create chat_messages table
        """CREATE TABLE IF NOT EXISTS chat_messages (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
            message_type VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            metadata JSONB DEFAULT '{}',
            referenced_chunks UUID[] DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );""",
        
        # Create indexes for processed_embeddings
        "CREATE INDEX IF NOT EXISTS idx_processed_embeddings_document_id ON processed_embeddings(document_id);",
        "CREATE INDEX IF NOT EXISTS idx_processed_embeddings_chunk_id ON processed_embeddings(chunk_id);",
        "CREATE INDEX IF NOT EXISTS idx_processed_embeddings_chunk_index ON processed_embeddings(chunk_index);",
        "CREATE INDEX IF NOT EXISTS idx_processed_embeddings_content_type ON processed_embeddings(content_type);",
        "CREATE INDEX IF NOT EXISTS idx_processed_embeddings_created_at ON processed_embeddings(created_at);",
        
        # Create GIN indexes for JSONB fields
        "CREATE INDEX IF NOT EXISTS idx_processed_embeddings_extracted_metadata ON processed_embeddings USING GIN (extracted_metadata);",
        "CREATE INDEX IF NOT EXISTS idx_processed_embeddings_chunk_metadata ON processed_embeddings USING GIN (chunk_metadata);",
        
        # Create indexes for chat tables
        "CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_chat_sessions_last_activity ON chat_sessions(last_activity);",
        "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);",
        "CREATE INDEX IF NOT EXISTS idx_chat_messages_message_type ON chat_messages(message_type);",
        "CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);",
    ]
    
    print("🔄 Creating missing tables...")
    
    for i, statement in enumerate(sql_statements, 1):
        print(f"   Executing statement {i}/{len(sql_statements)}...")
        try:
            # Execute the SQL statement using raw SQL
            result = client.rpc('exec_sql', {'sql': statement}).execute()
            print(f"   ✅ Statement {i} executed successfully")
        except Exception as e:
            # Try alternative execution method
            try:
                if 'CREATE TABLE' in statement.upper():
                    # For table creation, try using the table API
                    print(f"   ⚠️  Statement {i} may need manual execution: {str(e)[:100]}...")
                    print(f"   SQL: {statement[:100]}...")
                else:
                    print(f"   ❌ Statement {i} failed: {str(e)[:100]}...")
            except Exception as e2:
                print(f"   ❌ Statement {i} failed: {str(e2)[:100]}...")
    
    print("✅ Table creation completed!")
    return True

def check_tables():
    """Check if the required tables exist."""
    try:
        client = supabase_client.get_client()
        
        tables_to_check = [
            'documents',
            'processed_embeddings', 
            'chat_sessions',
            'chat_messages'
        ]
        
        all_exist = True
        
        for table in tables_to_check:
            try:
                result = client.table(table).select('id').limit(1).execute()
                print(f"✅ '{table}' table exists")
            except Exception as e:
                print(f"❌ '{table}' table not found: {e}")
                all_exist = False
        
        return all_exist
        
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Missing Tables Creation Tool")
    print("=" * 50)
    
    # Check current state
    print("\n🔍 Checking current table status...")
    if check_tables():
        print("\n✅ All required tables already exist!")
        print("You can now use the document processing API.")
    else:
        print("\n🔄 Creating missing tables...")
        if create_missing_tables():
            print("\n🔍 Verifying table creation...")
            if check_tables():
                print("\n🎉 All tables created successfully!")
                print("You can now use the document processing API.")
            else:
                print("\n⚠️  Some tables may still be missing.")
                print("Please check the error messages above.")
        else:
            print("\n❌ Table creation failed.")
            print("\n💡 Manual creation option:")
            print("1. Go to your Supabase dashboard")
            print("2. Open the SQL Editor")
            print("3. Copy and paste the SQL statements from the error messages above")
            print("4. Execute them one by one")
