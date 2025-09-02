#!/usr/bin/env python3
"""
Script to update the existing document with aggregated metadata from its chunks.
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

async def update_document_metadata():
    """Update the existing document with aggregated metadata."""
    
    print("🔄 Updating Document Metadata")
    print("=" * 50)
    
    if not supabase_client.is_available():
        print("❌ Supabase client not available")
        return
    
    client = supabase_client.get_client()
    document_id = "f67a63f5-5755-4a1e-814b-802a7aadccf5"
    
    # Get all chunks for this document
    print(f"📄 Getting chunks for document {document_id}...")
    try:
        chunks_response = client.table('langextract_processed_embeddings').select('*').eq('document_id', document_id).execute()
        chunks = chunks_response.data or []
        print(f"   Found {len(chunks)} chunks")
        
        if not chunks:
            print("   ❌ No chunks found for this document")
            return
        
    except Exception as e:
        print(f"   ❌ Error getting chunks: {e}")
        return
    
    # Convert chunks to the format expected by the processor
    print("🔄 Converting chunks to processor format...")
    processed_chunks = []
    for chunk in chunks:
        processed_chunk = {
            'id': chunk['id'],
            'document_id': chunk['document_id'],
            'chunk_id': chunk['chunk_id'],
            'chunk_index': chunk['chunk_index'],
            'content': chunk['content'],
            'content_type': chunk.get('content_type', 'text'),
            'chunk_metadata': chunk.get('chunk_metadata', {}),
            'extracted_metadata': chunk.get('extracted_metadata', {}),
            'embeddings': chunk.get('all_embeddings', {}),
            'created_at': chunk.get('created_at', '')
        }
        processed_chunks.append(processed_chunk)
    
    # Create processor instance and aggregate metadata
    print("🔄 Aggregating metadata...")
    processor = DocumentProcessor()
    try:
        document_metadata = await processor._aggregate_document_metadata(processed_chunks)
        print(f"   ✅ Aggregated metadata with {len(document_metadata)} fields")
        print(f"   📊 Total chunks: {document_metadata.get('total_chunks', 0)}")
        print(f"   📝 Key entities: {len(document_metadata.get('key_entities', []))}")
        print(f"   📋 Document sections: {len(document_metadata.get('content_insights', {}).get('document_sections', []))}")
        
    except Exception as e:
        print(f"   ❌ Error aggregating metadata: {e}")
        return
    
    # Update the document with the aggregated metadata
    print("🔄 Updating document record...")
    try:
        await processor._update_document_status(document_id, 'completed', metadata=document_metadata)
        print("   ✅ Document metadata updated successfully!")
        
    except Exception as e:
        print(f"   ❌ Error updating document: {e}")
        return
    
    # Verify the update
    print("🔍 Verifying update...")
    try:
        doc_response = client.table('langextract_documents').select('*').eq('id', document_id).execute()
        if doc_response.data:
            doc = doc_response.data[0]
            metadata = doc.get('metadata', {})
            print(f"   ✅ Document metadata now contains {len(metadata)} fields")
            if metadata:
                print(f"   📊 Primary document type: {metadata.get('document_type_indicators', {}).get('primary_type', 'Unknown')}")
                print(f"   📝 Total text length: {metadata.get('content_insights', {}).get('total_text_length', 0)}")
        else:
            print("   ❌ Document not found after update")
    except Exception as e:
        print(f"   ❌ Error verifying update: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(update_document_metadata())
