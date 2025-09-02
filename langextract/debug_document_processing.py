#!/usr/bin/env python3
"""
Debug script to check what happened during document processing.
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
from document_processor.processor import DocumentProcessor
import asyncio

async def debug_document_processing():
    """Debug what happened during document processing."""
    
    print("🔍 Debugging Document Processing")
    print("=" * 50)
    
    if not supabase_client.is_available():
        print("❌ Supabase client not available")
        return
    
    client = supabase_client.get_client()
    document_id = "f67a63f5-5755-4a1e-814b-802a7aadccf5"
    
    # Check the document record
    print("\n1. Document Record:")
    try:
        doc_response = client.table('langextract_documents').select('*').eq('id', document_id).execute()
        if doc_response.data:
            doc = doc_response.data[0]
            print(f"   ID: {doc['id']}")
            print(f"   Filename: {doc['filename']}")
            print(f"   Status: {doc['processing_status']}")
            print(f"   Error: {doc.get('processing_error', 'None')}")
            print(f"   File Path: {doc['file_path']}")
            print(f"   File Size: {doc['file_size']}")
            print(f"   Created: {doc['created_at']}")
            print(f"   Processed: {doc.get('processed_at', 'Not processed')}")
        else:
            print("   ❌ Document not found")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Check if the file exists
    print("\n2. File Existence:")
    file_path = doc['file_path']
    if os.path.exists(file_path):
        print(f"   ✅ File exists: {file_path}")
        file_size = os.path.getsize(file_path)
        print(f"   📊 File size: {file_size} bytes")
    else:
        print(f"   ❌ File not found: {file_path}")
        return
    
    # Try to reprocess the document
    print("\n3. Attempting to Reprocess Document:")
    try:
        processor = DocumentProcessor()
        
        # Read the file
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        print(f"   📄 Read {len(file_data)} bytes from file")
        
        # Process the document
        print("   🔄 Processing document...")
        result = await processor.process_document(
            file_data=file_data,
            filename=doc['filename'],
            user_id=doc['user_id'],
            schemas=['invoice', 'support_case']
        )
        
        print(f"   ✅ Processing completed!")
        print(f"   📊 Chunks processed: {result.get('chunks_processed', 0)}")
        print(f"   ⏱️  Processing time: {result.get('processing_time', 0):.2f}s")
        
    except Exception as e:
        print(f"   ❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Check if chunks were created
    print("\n4. Checking for Chunks:")
    try:
        chunks_response = client.table('langextract_processed_embeddings').select('*').eq('document_id', document_id).execute()
        chunks = chunks_response.data or []
        print(f"   Found {len(chunks)} chunks")
        
        if chunks:
            for i, chunk in enumerate(chunks[:3]):
                print(f"   Chunk {i+1}: {chunk['content'][:100]}...")
        else:
            print("   ❌ Still no chunks found")
    except Exception as e:
        print(f"   ❌ Error checking chunks: {e}")

if __name__ == "__main__":
    asyncio.run(debug_document_processing())
