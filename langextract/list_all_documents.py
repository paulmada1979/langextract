#!/usr/bin/env python3
"""
List all documents in the database to see what's available.
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

def list_all_documents():
    """List all documents in the database."""
    
    print("📄 Listing All Documents")
    print("=" * 50)
    
    if not supabase_client.is_available():
        print("❌ Supabase client not available")
        return
    
    client = supabase_client.get_client()
    
    try:
        # Get all documents
        docs_response = client.table('langextract_documents').select('*').order('created_at', desc=True).execute()
        documents = docs_response.data or []
        
        print(f"Found {len(documents)} documents:")
        
        if documents:
            for i, doc in enumerate(documents, 1):
                print(f"\n{i}. Document:")
                print(f"   ID: {doc['id']}")
                print(f"   Filename: {doc['filename']}")
                print(f"   Status: {doc['processing_status']}")
                print(f"   User ID: {doc['user_id']}")
                print(f"   Created: {doc['created_at']}")
                print(f"   Error: {doc.get('processing_error', 'None')}")
        else:
            print("   ❌ No documents found in database")
            
    except Exception as e:
        print(f"❌ Error listing documents: {e}")
        return
    
    # Also check embeddings
    print(f"\n📊 Checking Embeddings:")
    try:
        emb_response = client.table('langextract_processed_embeddings').select('document_id').execute()
        embeddings = emb_response.data or []
        
        if embeddings:
            unique_docs = set(emb['document_id'] for emb in embeddings)
            print(f"   Found embeddings for {len(unique_docs)} documents:")
            for doc_id in unique_docs:
                print(f"   - {doc_id}")
        else:
            print("   ❌ No embeddings found")
            
    except Exception as e:
        print(f"   ❌ Error checking embeddings: {e}")

if __name__ == "__main__":
    list_all_documents()
