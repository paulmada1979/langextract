#!/usr/bin/env python3
"""
Script to completely reset the embeddings feature in Supabase.
This script will:
1. Remove the embeddings table and all related functions
2. Recreate everything fresh with the correct column names
3. Verify the setup is working
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

def execute_sql_file(conn, file_path):
    """Execute SQL commands from a file."""
    try:
        with open(file_path, 'r') as file:
            sql_commands = file.read()
        
        cursor = conn.cursor()
        
        # Split by semicolon and execute each command
        commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip()]
        
        for i, command in enumerate(commands):
            if command:
                print(f"Executing command {i+1}/{len(commands)}...")
                cursor.execute(command)
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"Error executing SQL file: {e}")
        return False

def verify_setup(conn):
    """Verify that the embeddings setup is working correctly."""
    try:
        cursor = conn.cursor()
        
        print("\n" + "="*50)
        print("VERIFICATION RESULTS")
        print("="*50)
        
        # Check table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'embeddings' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\n📋 Table Structure:")
        for col_name, data_type in columns:
            print(f"  - {col_name}: {data_type}")
        
        # Check function exists
        cursor.execute("""
            SELECT routine_name, routine_type 
            FROM information_schema.routines 
            WHERE routine_name = 'match_embeddings';
        """)
        
        functions = cursor.fetchall()
        print(f"\n🔧 Functions: {len(functions)} found")
        for func_name, func_type in functions:
            print(f"  - {func_name} ({func_type})")
        
        # Test the function
        cursor.execute("""
            SELECT COUNT(*) FROM match_embeddings(
                array_fill(0.1::real, ARRAY[1536])::vector(1536),
                0.5,
                1
            );
        """)
        
        result = cursor.fetchone()
        print(f"\n✅ Function Test: {result[0]} results returned")
        
        # Check indexes
        cursor.execute("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'embeddings';
        """)
        
        indexes = cursor.fetchall()
        print(f"\n📊 Indexes: {len(indexes)} created")
        for idx_name, idx_def in indexes:
            print(f"  - {idx_name}")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"Verification failed: {e}")
        return False

def main():
    """Main function to reset the embeddings feature."""
    print("🔄 Embeddings Feature Reset")
    print("=" * 40)
    
    # Confirm reset
    response = input("⚠️  This will DELETE the embeddings table and all data. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Reset cancelled.")
        sys.exit(0)
    
    # Get database connection
    conn = get_database_connection()
    if not conn:
        print("Failed to connect to database. Please check your environment variables:")
        print("  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        sys.exit(1)
    
    try:
        print("\n🗑️  Starting cleanup and re-initialization...")
        
        # Execute the reset SQL
        sql_file = os.path.join(os.path.dirname(__file__), 'reset_embeddings_feature.sql')
        if not os.path.exists(sql_file):
            print(f"SQL file not found: {sql_file}")
            sys.exit(1)
        
        success = execute_sql_file(conn, sql_file)
        if not success:
            print("❌ Reset failed!")
            sys.exit(1)
        
        print("\n✅ Reset completed successfully!")
        
        # Verify the setup
        verify_setup(conn)
        
        print("\n🎉 Embeddings feature has been completely reset and re-initialized!")
        print("\nNext steps:")
        print("1. Update your Langflow template to use: Content: {content}")
        print("2. Test your embeddings storage and retrieval")
        print("3. Verify your Supabase component is working")
        
    except Exception as e:
        print(f"Reset failed: {e}")
        sys.exit(1)
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
