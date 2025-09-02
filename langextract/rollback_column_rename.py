#!/usr/bin/env python3
"""
Script to rollback column rename migration for the embeddings table.
This script renames back:
- embedding -> text_embedding
- content -> original_text
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def get_database_connection():
    """Get database connection from environment variables."""
    try:
        # Try to get connection details from environment
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'langextract')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        
        # Create connection
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        # Set isolation level to autocommit for DDL operations
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        return conn
        
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return None

def rollback_migration(conn):
    """Rollback the column rename migration."""
    try:
        cursor = conn.cursor()
        
        print("Starting column rename rollback...")
        
        # Check if columns exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'embeddings' 
            AND column_name IN ('embedding', 'content')
            ORDER BY column_name;
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"Existing columns: {existing_columns}")
        
        # Rename embedding back to text_embedding
        if 'embedding' in existing_columns:
            print("Renaming embedding back to text_embedding...")
            cursor.execute("ALTER TABLE embeddings RENAME COLUMN embedding TO text_embedding;")
            print("✓ embedding renamed back to text_embedding")
        else:
            print("Column embedding not found, skipping...")
        
        # Rename content back to original_text
        if 'content' in existing_columns:
            print("Renaming content back to original_text...")
            cursor.execute("ALTER TABLE embeddings RENAME COLUMN content TO original_text;")
            print("✓ content renamed back to original_text")
        else:
            print("Column content not found, skipping...")
        
        # Restore the original match_embeddings function
        print("Restoring original match_embeddings function...")
        cursor.execute("""
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
        """)
        print("✓ match_embeddings function restored")
        
        # Restore original column comments
        print("Restoring original column comments...")
        cursor.execute("COMMENT ON COLUMN embeddings.text_embedding IS 'Primary embedding vector for similarity search (OpenAI text-embedding-3-small)';")
        cursor.execute("COMMENT ON COLUMN embeddings.original_text IS 'Original text content of the document chunk';")
        print("✓ Column comments restored")
        
        # Verify the rollback
        print("\nVerifying rollback...")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'embeddings' 
            AND column_name IN ('text_embedding', 'original_text')
            ORDER BY column_name;
        """)
        
        restored_columns = cursor.fetchall()
        print("Restored column structure:")
        for column_name, data_type in restored_columns:
            print(f"  - {column_name}: {data_type}")
        
        cursor.close()
        print("\n✓ Rollback completed successfully!")
        
    except Exception as e:
        print(f"Rollback failed: {e}")
        conn.rollback()
        raise

def main():
    """Main function to run the rollback."""
    print("LangExtract Column Rename Rollback")
    print("=" * 40)
    
    # Confirm rollback
    response = input("Are you sure you want to rollback the column rename migration? (yes/no): ")
    if response.lower() != 'yes':
        print("Rollback cancelled.")
        sys.exit(0)
    
    # Get database connection
    conn = get_database_connection()
    if not conn:
        print("Failed to connect to database. Please check your environment variables:")
        print("  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        sys.exit(1)
    
    try:
        # Apply the rollback
        rollback_migration(conn)
        
    except Exception as e:
        print(f"Rollback failed: {e}")
        sys.exit(1)
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
