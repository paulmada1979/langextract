#!/usr/bin/env python3
"""
Test the search function directly to see if it's working.
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

def test_search_function():
    """Test the search function directly."""
    
    print("🔍 Testing Search Function")
    print("=" * 50)
    
    if not supabase_client.is_available():
        print("❌ Supabase client not available")
        return
    
    if not openai_client.is_available():
        print("❌ OpenAI client not available")
        return
    
    client = supabase_client.get_client()
    user_id = "2e4d6dc7-1050-425b-a9e7-f717aed867de"
    document_id = "09545519-8bde-401a-b0a6-3a35469aa523"
    
    # 1. Check embeddings exist
    print("\n1. Checking embeddings...")
    try:
        emb_response = client.table('langextract_processed_embeddings').select('*').eq('user_id', user_id).execute()
        embeddings = emb_response.data or []
        print(f"   Found {len(embeddings)} embeddings for user {user_id}")
        
        if embeddings:
            for i, emb in enumerate(embeddings[:3]):
                print(f"   Chunk {i+1}: {emb['content'][:100]}...")
                print(f"     - Has embedding: {'Yes' if emb.get('embedding') else 'No'}")
                if emb.get('embedding'):
                    print(f"     - Embedding dimensions: {len(emb['embedding'])}")
        else:
            print("   ❌ No embeddings found")
            return
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # 2. Generate query embedding
    print("\n2. Generating query embedding...")
    test_query = "What is this document about?"
    try:
        query_embedding = openai_client.generate_embedding(test_query)
        if query_embedding:
            print(f"   ✅ Generated embedding with {len(query_embedding)} dimensions")
        else:
            print("   ❌ Failed to generate embedding")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # 3. Test search function
    print("\n3. Testing search function...")
    try:
        search_params = {
            'query_embedding': query_embedding,
            'filter_user_id': user_id,
            'document_ids': None,
            'match_threshold': 0.1,  # Very low threshold for testing
            'match_count': 10
        }
        
        print(f"   Search params: {search_params}")
        
        search_response = client.rpc('search_langextract_processed_embeddings', search_params).execute()
        results = search_response.data or []
        print(f"   Found {len(results)} search results")
        
        if results:
            for i, result in enumerate(results[:3]):
                print(f"   Result {i+1}:")
                print(f"     - Similarity: {result.get('similarity', 'N/A')}")
                print(f"     - Content: {result['content'][:100]}...")
                print(f"     - Document ID: {result.get('document_id', 'N/A')}")
        else:
            print("   ❌ No search results")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Test with specific document ID
    print("\n4. Testing with specific document ID...")
    try:
        search_params = {
            'query_embedding': query_embedding,
            'filter_user_id': user_id,
            'document_ids': [document_id],
            'match_threshold': 0.1,
            'match_count': 10
        }
        
        search_response = client.rpc('search_langextract_processed_embeddings', search_params).execute()
        results = search_response.data or []
        print(f"   Found {len(results)} search results for document {document_id}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_search_function()
