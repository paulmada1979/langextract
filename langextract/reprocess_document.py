#!/usr/bin/env python3
"""
Reprocess the document with proper docling extraction.
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

async def reprocess_document():
    """Reprocess the document with proper docling extraction."""
    
    print("🔄 Reprocessing Document with Docling")
    print("=" * 50)
    
    if not supabase_client.is_available():
        print("❌ Supabase client not available")
        return
    
    client = supabase_client.get_client()
    document_id = "09545519-8bde-401a-b0a6-3a35469aa523"
    user_id = "2e4d6dc7-1050-425b-a9e7-f717aed867de"
    
    # Get the document record
    print("📄 Getting document record...")
    try:
        doc_response = client.table('langextract_documents').select('*').eq('id', document_id).execute()
        if not doc_response.data:
            print("   ❌ Document not found")
            return
        
        doc = doc_response.data[0]
        print(f"   ✅ Found document: {doc['filename']}")
        print(f"   📁 File path: {doc['file_path']}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Check if file exists
    file_path = doc['file_path']
    if not os.path.exists(file_path):
        print(f"   ❌ File not found: {file_path}")
        return
    
    print(f"   ✅ File exists: {file_path}")
    
    # Delete existing chunks
    print("🗑️  Deleting existing chunks...")
    try:
        client.table('langextract_processed_embeddings').delete().eq('document_id', document_id).execute()
        print("   ✅ Deleted existing chunks")
    except Exception as e:
        print(f"   ❌ Error deleting chunks: {e}")
        return
    
    # Read the file
    print("📖 Reading file...")
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        print(f"   ✅ Read {len(file_data)} bytes")
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        return
    
    # Reprocess the document
    print("🔄 Reprocessing document with docling...")
    try:
        processor = DocumentProcessor()
        
        result = await processor.process_document(
            file_data=file_data,
            filename=doc['filename'],
            user_id=user_id,
            schemas=['invoice', 'support_case']
        )
        
        print(f"   ✅ Processing completed!")
        print(f"   📊 Chunks processed: {result.get('chunks_processed', 0)}")
        print(f"   ⏱️  Processing time: {result.get('processing_time', 0):.2f}s")
        
        # Show sample chunks
        chunks = result.get('chunks', [])
        if chunks:
            print(f"   📝 Sample chunks:")
            for i, chunk in enumerate(chunks[:3]):
                content = chunk.get('content', '')
                print(f"     Chunk {i+1}: {content[:100]}...")
        
    except Exception as e:
        print(f"   ❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Verify the reprocessing
    print("🔍 Verifying reprocessing...")
    try:
        chunks_response = client.table('langextract_processed_embeddings').select('*').eq('document_id', document_id).execute()
        chunks = chunks_response.data or []
        print(f"   ✅ Found {len(chunks)} new chunks")
        
        if chunks:
            for i, chunk in enumerate(chunks[:3]):
                content = chunk['content']
                embedding = chunk.get('embedding', [])
                print(f"   Chunk {i+1}:")
                print(f"     - Content: {content[:100]}...")
                print(f"     - Embedding dimensions: {len(embedding)}")
                print(f"     - Has valid content: {'Yes' if content and not content.startswith('[File type') else 'No'}")
        
    except Exception as e:
        print(f"   ❌ Error verifying: {e}")

if __name__ == "__main__":
    asyncio.run(reprocess_document())
