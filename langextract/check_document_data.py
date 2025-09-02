#!/usr/bin/env python3
"""
Check what data was actually stored for the uploaded document.
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

def check_document_data():
    """Check what data was stored for the uploaded document."""
    
    print("🔍 Checking Document Data")
    print("=" * 50)
    
    if not supabase_client.is_available():
        print("❌ Supabase client not available")
        return
    
    client = supabase_client.get_client()
    
    # Check the document
    print("\n1. Document Record:")
    try:
        doc_response = client.table('langextract_documents').select('*').eq('id', 'f67a63f5-5755-4a1e-814b-802a7aadccf5').execute()
        if doc_response.data:
            doc = doc_response.data[0]
            print(f"   ID: {doc['id']}")
            print(f"   Filename: {doc['filename']}")
            print(f"   Status: {doc['processing_status']}")
            print(f"   Metadata: {doc['metadata']}")
            print(f"   User ID: {doc['user_id']}")
        else:
            print("   ❌ Document not found")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Check embeddings
    print("\n2. Processed Embeddings:")
    try:
        emb_response = client.table('langextract_processed_embeddings').select('*').eq('document_id', 'f67a63f5-5755-4a1e-814b-802a7aadccf5').execute()
        embeddings = emb_response.data or []
        print(f"   Found {len(embeddings)} embeddings")
        
        if embeddings:
            for i, emb in enumerate(embeddings[:3]):
                print(f"   Chunk {i+1}:")
                print(f"     - Content: {emb['content'][:100]}...")
                print(f"     - Extracted Metadata: {emb.get('extracted_metadata', {})}")
                print(f"     - Has Embedding: {'Yes' if emb.get('embedding') else 'No'}")
                if emb.get('embedding'):
                    print(f"     - Embedding Dimensions: {len(emb['embedding'])}")
        else:
            print("   ❌ No embeddings found")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    check_document_data()
