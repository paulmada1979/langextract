#!/usr/bin/env python3
"""
Script to apply column rename migration for the embeddings table.
This script renames:
- text_embedding -> embedding
- original_text -> content
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

def apply_migration(conn):
    """Apply the column rename migration."""
    try:
        cursor = conn.cursor()
        
        print("Starting column rename migration...")
        
        # Check if columns exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'embeddings' 
            AND column_name IN ('text_embedding', 'original_text')
            ORDER BY column_name;
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"Existing columns: {existing_columns}")
        
        # Rename text_embedding to embedding
        if 'text_embedding' in existing_columns:
            print("Renaming text_embedding to embedding...")
            cursor.execute("ALTER TABLE embeddings RENAME COLUMN text_embedding TO embedding;")
            print("✓ text_embedding renamed to embedding")
        else:
            print("Column text_embedding not found, skipping...")
        
        # Rename original_text to content
        if 'original_text' in existing_columns:
            print("Renaming original_text to content...")
            cursor.execute("ALTER TABLE embeddings RENAME COLUMN original_text TO content;")
            print("✓ original_text renamed to content")
        else:
            print("Column original_text not found, skipping...")
        
        # Update the match_embeddings function
        print("Updating match_embeddings function...")
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
        """)
        print("✓ match_embeddings function updated")
        
        # Update column comments
        print("Updating column comments...")
        cursor.execute("COMMENT ON COLUMN embeddings.embedding IS 'Primary embedding vector for similarity search (OpenAI text-embedding-3-small)';")
        cursor.execute("COMMENT ON COLUMN embeddings.content IS 'Original text content of the document chunk';")
        print("✓ Column comments updated")
        
        # Verify the changes
        print("\nVerifying changes...")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'embeddings' 
            AND column_name IN ('embedding', 'content')
            ORDER BY column_name;
        """)
        
        new_columns = cursor.fetchall()
        print("New column structure:")
        for column_name, data_type in new_columns:
            print(f"  - {column_name}: {data_type}")
        
        cursor.close()
        print("\n✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        raise

def main():
    """Main function to run the migration."""
    print("LangExtract Column Rename Migration")
    print("=" * 40)
    
    # Get database connection
    conn = get_database_connection()
    if not conn:
        print("Failed to connect to database. Please check your environment variables:")
        print("  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        sys.exit(1)
    
    try:
        # Apply the migration
        apply_migration(conn)
        
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
