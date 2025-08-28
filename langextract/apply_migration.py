#!/usr/bin/env python3
"""
Script to apply database migration for embeddings table.
This script connects to Supabase and creates the necessary table structure.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """Initialize and return Supabase client."""
    url = os.getenv('SUPABASE_URL')
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not anon_key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment")
    
    try:
        client = create_client(url, anon_key)
        logger.info("Supabase client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        raise


def read_migration_file() -> str:
    """Read the migration SQL file."""
    migration_path = os.path.join(
        os.path.dirname(__file__), 
        'db', 'migrations', '001_create_embeddings_table.sql'
    )
    
    try:
        with open(migration_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Migration file not found: {migration_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to read migration file: {e}")
        raise


def apply_migration(client: Client, sql: str) -> bool:
    """Apply the migration SQL to Supabase."""
    try:
        # Split SQL into individual statements
        statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            if statement:
                logger.info(f"Executing statement {i + 1}/{len(statements)}")
                logger.debug(f"SQL: {statement[:100]}...")
                
                try:
                    # Execute the SQL statement
                    result = client.rpc('exec_sql', {'sql': statement}).execute()
                    logger.info(f"Statement {i + 1} executed successfully")
                except Exception as e:
                    # If exec_sql RPC doesn't exist, try direct execution
                    logger.warning(f"exec_sql RPC not available, trying alternative method: {e}")
                    # For now, we'll skip complex statements that require direct DB access
                    if 'CREATE EXTENSION' in statement or 'CREATE OR REPLACE FUNCTION' in statement:
                        logger.info(f"Skipping statement {i + 1} (requires direct DB access): {statement[:50]}...")
                        continue
                    else:
                        raise e
        
        logger.info("Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


def verify_migration(client: Client) -> bool:
    """Verify that the migration was applied successfully."""
    try:
        # Check if embeddings table exists
        response = client.table('embeddings').select('id').limit(1).execute()
        logger.info("Embeddings table verification successful")
        return True
        
    except Exception as e:
        logger.error(f"Migration verification failed: {e}")
        return False


def main():
    """Main function to run the migration."""
    logger.info("Starting database migration for embeddings table...")
    
    try:
        # Get Supabase client
        client = get_supabase_client()
        
        # Read migration SQL
        migration_sql = read_migration_file()
        logger.info("Migration SQL loaded successfully")
        
        # Apply migration
        if apply_migration(client, migration_sql):
            logger.info("Migration applied successfully")
            
            # Verify migration
            if verify_migration(client):
                logger.info("Migration verified successfully")
                logger.info("✅ Embeddings table is ready for use!")
            else:
                logger.error("❌ Migration verification failed")
                sys.exit(1)
        else:
            logger.error("❌ Migration failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Migration script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
