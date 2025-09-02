#!/usr/bin/env python3
"""
Debug script to check why search returns 0 results.
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
from core.openai_client import openai_client

def debug_search_issue(user_id="2e4d6dc7-1050-425b-a9e9-f717aed867de"):
    """Debug why search returns 0 results."""
    
    print("🔍 Debugging Search Issue")
    print("=" * 50)
    print(f"User ID: {user_id}")
    
    if not supabase_client.is_available():
        print("❌ Supabase client not available")
        return
    
    client = supabase_client.get_client()
    
    # 1. Check if user has any documents
    print("\n1. Checking user documents...")
    try:
        docs_response = client.table('langextract_documents').select('*').eq('user_id', user_id).execute()
        documents = docs_response.data or []
        print(f"   Found {len(documents)} documents for user")
        
        if documents:
            for doc in documents:
                print(f"   - {doc['filename']} (Status: {doc['processing_status']})")
        else:
            print("   ❌ No documents found for this user")
            return
            
    except Exception as e:
        print(f"   ❌ Error checking documents: {e}")
        return
    
    # 2. Check if documents have processed embeddings
    print("\n2. Checking processed embeddings...")
    try:
        embeddings_response = client.table('langextract_processed_embeddings').select('*').eq('user_id', user_id).execute()
        embeddings = embeddings_response.data or []
        print(f"   Found {len(embeddings)} embeddings for user")
        
        if embeddings:
            for emb in embeddings[:3]:  # Show first 3
                print(f"   - Chunk {emb['chunk_index']}: {emb['content'][:50]}...")
        else:
            print("   ❌ No embeddings found for this user")
            return
            
    except Exception as e:
        print(f"   ❌ Error checking embeddings: {e}")
        return
    
    # 3. Test embedding generation
    print("\n3. Testing embedding generation...")
    if not openai_client.is_available():
        print("   ❌ OpenAI client not available")
        return
    
    test_query = "Is it an invoice?"
    try:
        query_embedding = openai_client.generate_embedding(test_query)
        if query_embedding:
            print(f"   ✅ Generated embedding with {len(query_embedding)} dimensions")
        else:
            print("   ❌ Failed to generate embedding")
            return
    except Exception as e:
        print(f"   ❌ Error generating embedding: {e}")
        return
    
    # 4. Test the search function directly
    print("\n4. Testing search function...")
    try:
        search_params = {
            'query_embedding': query_embedding,
            'filter_user_id': user_id,
            'document_ids': None,
            'match_threshold': 0.1,  # Lower threshold for testing
            'match_count': 10
        }
        
        search_response = client.rpc('search_langextract_processed_embeddings', search_params).execute()
        results = search_response.data or []
        print(f"   Found {len(results)} search results")
        
        if results:
            for result in results[:3]:
                print(f"   - Similarity: {result.get('similarity', 'N/A'):.3f}, Content: {result['content'][:50]}...")
        else:
            print("   ❌ Search function returned 0 results")
            
    except Exception as e:
        print(f"   ❌ Error testing search function: {e}")
        return
    
    # 5. Check if embeddings have valid vectors
    print("\n5. Checking embedding vectors...")
    try:
        # Get a sample embedding to check
        sample_emb = embeddings[0] if embeddings else None
        if sample_emb and 'embedding' in sample_emb:
            embedding_vector = sample_emb['embedding']
            if embedding_vector:
                print(f"   ✅ Sample embedding has {len(embedding_vector)} dimensions")
            else:
                print("   ❌ Sample embedding is empty")
        else:
            print("   ❌ No embedding vector found in sample")
            
    except Exception as e:
        print(f"   ❌ Error checking embedding vectors: {e}")
    
    print("\n🎯 Debug Summary:")
    print(f"   - Documents: {len(documents)}")
    print(f"   - Embeddings: {len(embeddings)}")
    print(f"   - Search Results: {len(results) if 'results' in locals() else 'Not tested'}")

if __name__ == "__main__":
    debug_search_issue()
