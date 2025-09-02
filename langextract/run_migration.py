#!/usr/bin/env python3
"""
Script to run the document processing tables migration.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.supabase_client import supabase_client

def run_migration():
    """Run the document processing tables migration."""
    
    if not supabase_client.is_available():
        print("❌ Supabase client not available. Please check your environment variables:")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_ANON_KEY")
        return False
    
    # Read the migration SQL file
    migration_file = project_root / "db" / "migrations" / "003_create_document_processing_tables.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    try:
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("🔄 Running document processing tables migration...")
        
        # Split the SQL into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        client = supabase_client.get_client()
        
        for i, statement in enumerate(statements, 1):
            if statement:
                print(f"   Executing statement {i}/{len(statements)}...")
                try:
                    # Execute the SQL statement
                    result = client.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"   ✅ Statement {i} executed successfully")
                except Exception as e:
                    # Try direct execution for some statements
                    try:
                        if 'CREATE TABLE' in statement.upper():
                            # For table creation, we might need to use a different approach
                            print(f"   ⚠️  Statement {i} may need manual execution: {str(e)[:100]}...")
                        else:
                            print(f"   ❌ Statement {i} failed: {str(e)[:100]}...")
                    except Exception as e2:
                        print(f"   ❌ Statement {i} failed: {str(e2)[:100]}...")
        
        print("✅ Migration completed!")
        print("\n📋 Next steps:")
        print("1. Verify the tables were created in your Supabase dashboard")
        print("2. Test the document upload functionality")
        print("3. Access the chat interface at: /api/document/chat/")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def check_tables():
    """Check if the required tables exist."""
    try:
        client = supabase_client.get_client()
        
        # Check if documents table exists
        try:
            result = client.table('documents').select('id').limit(1).execute()
            print("✅ 'documents' table exists")
        except Exception as e:
            print(f"❌ 'documents' table not found: {e}")
            return False
        
        # Check if processed_embeddings table exists
        try:
            result = client.table('processed_embeddings').select('id').limit(1).execute()
            print("✅ 'processed_embeddings' table exists")
        except Exception as e:
            print(f"❌ 'processed_embeddings' table not found: {e}")
            return False
        
        # Check if chat_sessions table exists
        try:
            result = client.table('chat_sessions').select('id').limit(1).execute()
            print("✅ 'chat_sessions' table exists")
        except Exception as e:
            print(f"❌ 'chat_sessions' table not found: {e}")
            return False
        
        # Check if chat_messages table exists
        try:
            result = client.table('chat_messages').select('id').limit(1).execute()
            print("✅ 'chat_messages' table exists")
        except Exception as e:
            print(f"❌ 'chat_messages' table not found: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Document Processing Migration Tool")
    print("=" * 50)
    
    # Check if tables already exist
    print("\n🔍 Checking existing tables...")
    if check_tables():
        print("\n✅ All required tables already exist!")
        print("You can now use the document processing API.")
    else:
        print("\n🔄 Running migration...")
        if run_migration():
            print("\n🔍 Verifying migration...")
            check_tables()
        else:
            print("\n❌ Migration failed. Please check the error messages above.")
            print("\n💡 Manual migration option:")
            print("1. Go to your Supabase dashboard")
            print("2. Open the SQL Editor")
            print("3. Copy and paste the contents of:")
            print(f"   {project_root}/db/migrations/003_create_document_processing_tables.sql")
            print("4. Execute the SQL")
