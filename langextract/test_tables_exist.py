#!/usr/bin/env python3
"""
Test script to verify that the langextract_ tables exist.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'langextract.settings')

import django
django.setup()

from core.supabase_client import supabase_client

def test_tables_exist():
    """Test that all required langextract_ tables exist."""
    
    print("🧪 Testing Langextract Tables Existence")
    print("=" * 50)
    
    if not supabase_client.is_available():
        print("❌ Supabase client not available")
        return False
    
    client = supabase_client.get_client()
    
    tables_to_check = [
        'langextract_documents',
        'langextract_processed_embeddings', 
        'langextract_chat_sessions',
        'langextract_chat_messages'
    ]
    
    print("🔍 Checking table existence...")
    existing_tables = []
    
    for table in tables_to_check:
        try:
            # Try to select from the table (limit 0 to avoid data transfer)
            result = client.table(table).select('*').limit(0).execute()
            existing_tables.append(table)
            print(f"   ✅ Table '{table}' exists and is accessible")
        except Exception as e:
            print(f"   ❌ Table '{table}' not found: {str(e)[:100]}...")
    
    print(f"\n📊 Summary: {len(existing_tables)}/{len(tables_to_check)} tables exist")
    
    if len(existing_tables) == len(tables_to_check):
        print("\n🎉 All required tables exist!")
        print("You can now try uploading documents.")
        return True
    else:
        print("\n❌ Some tables are missing.")
        print("Please run the SQL migration in Supabase:")
        print("1. Go to your Supabase SQL Editor")
        print("2. Copy and paste the contents of: langextract/create_langextract_tables.sql")
        print("3. Run the SQL")
        return False

if __name__ == "__main__":
    success = test_tables_exist()
    
    if not success:
        print("\n⚠️ Please create the tables first before testing document upload.")
