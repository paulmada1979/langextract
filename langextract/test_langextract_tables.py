#!/usr/bin/env python3
"""
Test script to verify langextract_ prefixed tables functionality.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.supabase_client import supabase_client

def test_langextract_tables():
    """Test the langextract_ prefixed tables with a simple insert."""
    
    if not supabase_client.is_available():
        print("❌ Supabase client not available")
        return False
    
    client = supabase_client.get_client()
    
    try:
        # Test data for langextract_documents table
        test_document_data = {
            'filename': 'test_document.txt',
            'original_filename': 'test_document.txt',
            'file_type': 'txt',
            'file_size': 1024,
            'file_path': '/tmp/test_document.txt',
            'upload_status': 'uploaded',
            'processing_status': 'pending',
            'metadata': {}
        }
        
        print("🧪 Testing langextract_documents table insert...")
        print(f"Test data: {test_document_data}")
        
        # Try to insert the test document
        doc_result = client.table('langextract_documents').insert(test_document_data).execute()
        
        if doc_result.data:
            print("✅ Test document insert successful!")
            document_id = doc_result.data[0]['id']
            print(f"Inserted document ID: {document_id}")
            
            # Test processed_embeddings insert
            test_chunk_data = {
                'document_id': document_id,
                'chunk_id': 'test_chunk_1',
                'chunk_index': 0,
                'content': 'This is a test chunk content.',
                'content_type': 'text',
                'extracted_metadata': {},
                'chunk_metadata': {}
            }
            
            print("🧪 Testing langextract_processed_embeddings table insert...")
            chunk_result = client.table('langextract_processed_embeddings').insert(test_chunk_data).execute()
            
            if chunk_result.data:
                print("✅ Test chunk insert successful!")
                chunk_id = chunk_result.data[0]['id']
                print(f"Inserted chunk ID: {chunk_id}")
                
                # Test chat_sessions insert
                test_session_data = {
                    'session_name': 'Test Chat Session',
                    'document_ids': [document_id]
                }
                
                print("🧪 Testing langextract_chat_sessions table insert...")
                session_result = client.table('langextract_chat_sessions').insert(test_session_data).execute()
                
                if session_result.data:
                    print("✅ Test session insert successful!")
                    session_id = session_result.data[0]['id']
                    print(f"Inserted session ID: {session_id}")
                    
                    # Test chat_messages insert
                    test_message_data = {
                        'session_id': session_id,
                        'message_type': 'user',
                        'content': 'Hello, this is a test message.',
                        'metadata': {}
                    }
                    
                    print("🧪 Testing langextract_chat_messages table insert...")
                    message_result = client.table('langextract_chat_messages').insert(test_message_data).execute()
                    
                    if message_result.data:
                        print("✅ Test message insert successful!")
                        message_id = message_result.data[0]['id']
                        print(f"Inserted message ID: {message_id}")
                        
                        # Clean up - delete in reverse order due to foreign key constraints
                        print("🧹 Cleaning up test data...")
                        client.table('langextract_chat_messages').delete().eq('id', message_id).execute()
                        client.table('langextract_chat_sessions').delete().eq('id', session_id).execute()
                        client.table('langextract_processed_embeddings').delete().eq('id', chunk_id).execute()
                        client.table('langextract_documents').delete().eq('id', document_id).execute()
                        print("✅ Test data cleaned up")
                        
                        return True
                    else:
                        print("❌ Test message insert failed")
                        return False
                else:
                    print("❌ Test session insert failed")
                    return False
            else:
                print("❌ Test chunk insert failed")
                return False
        else:
            print("❌ Test document insert failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def check_table_schema():
    """Check the actual table schema for langextract_ tables."""
    
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
    
    print("🔍 Checking langextract_ table schemas...")
    accessible_tables = []
    
    for table in tables_to_check:
        try:
            test_result = client.table(table).select('*').limit(0).execute()
            accessible_tables.append(table)
            print(f"   ✅ Table '{table}' is accessible")
        except Exception as e:
            print(f"   ❌ Table '{table}' not accessible: {str(e)[:100]}...")
    
    print(f"\n📊 Summary: {len(accessible_tables)}/{len(tables_to_check)} tables are accessible")
    return accessible_tables

if __name__ == "__main__":
    print("🚀 Langextract Tables Test Suite")
    print("=" * 50)
    
    # Check table schemas
    print("\n1. Checking table schemas...")
    accessible_tables = check_table_schema()
    
    if len(accessible_tables) == 4:  # All 4 tables should be accessible
        print("\n2. Testing table inserts...")
        if test_langextract_tables():
            print("\n🎉 All langextract_ tables are working correctly!")
            print("You should be able to upload documents now.")
        else:
            print("\n❌ Table insert tests failed.")
            print("Please run the SQL migration in Supabase.")
    else:
        print("\n❌ Not all tables are accessible.")
        print("Please run the SQL migration in Supabase.")
        print("Run the SQL from: langextract/db/migrations/004_create_langextract_tables.sql")
