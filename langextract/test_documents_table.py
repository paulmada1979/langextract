#!/usr/bin/env python3
"""
Test script to verify documents table functionality.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.supabase_client import supabase_client

def test_documents_table():
    """Test the documents table with a simple insert."""
    
    if not supabase_client.is_available():
        print("❌ Supabase client not available")
        return False
    
    client = supabase_client.get_client()
    
    try:
        # Test data that matches our expected schema
        test_data = {
            'filename': 'test_document.txt',
            'original_filename': 'test_document.txt',
            'file_type': 'txt',
            'file_size': 1024,
            'file_path': '/tmp/test_document.txt',
            'upload_status': 'uploaded',
            'processing_status': 'pending',
            'metadata': {}
        }
        
        print("🧪 Testing documents table insert...")
        print(f"Test data: {test_data}")
        
        # Try to insert the test data
        result = client.table('documents').insert(test_data).execute()
        
        if result.data:
            print("✅ Test insert successful!")
            print(f"Inserted record ID: {result.data[0]['id']}")
            
            # Clean up - delete the test record
            test_id = result.data[0]['id']
            delete_result = client.table('documents').delete().eq('id', test_id).execute()
            print("✅ Test record cleaned up")
            
            return True
        else:
            print("❌ Test insert failed - no data returned")
            return False
            
    except Exception as e:
        print(f"❌ Test insert failed: {e}")
        return False

def check_table_schema():
    """Check the actual table schema."""
    
    if not supabase_client.is_available():
        print("❌ Supabase client not available")
        return False
    
    client = supabase_client.get_client()
    
    try:
        # Try to get table info by selecting all columns
        result = client.table('documents').select('*').limit(0).execute()
        print("✅ Documents table is accessible")
        
        # Try to get the table structure by attempting to select specific columns
        columns_to_test = [
            'id', 'filename', 'original_filename', 'file_type', 'file_size', 
            'file_path', 'upload_status', 'processing_status', 'processing_error',
            'created_at', 'updated_at', 'processed_at', 'metadata'
        ]
        
        print("🔍 Testing individual columns...")
        accessible_columns = []
        
        for column in columns_to_test:
            try:
                test_result = client.table('documents').select(column).limit(1).execute()
                accessible_columns.append(column)
                print(f"   ✅ Column '{column}' is accessible")
            except Exception as e:
                print(f"   ❌ Column '{column}' not accessible: {str(e)[:100]}...")
        
        print(f"\n📊 Summary: {len(accessible_columns)}/{len(columns_to_test)} columns are accessible")
        return accessible_columns
        
    except Exception as e:
        print(f"❌ Error checking table schema: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Documents Table Test Suite")
    print("=" * 50)
    
    # Check table schema
    print("\n1. Checking table schema...")
    accessible_columns = check_table_schema()
    
    if accessible_columns:
        print("\n2. Testing table insert...")
        if test_documents_table():
            print("\n🎉 Documents table is working correctly!")
            print("You should be able to upload documents now.")
        else:
            print("\n❌ Documents table insert test failed.")
            print("Please run the SQL fix script in Supabase.")
    else:
        print("\n❌ Table schema check failed.")
        print("Please run the SQL fix script in Supabase.")
