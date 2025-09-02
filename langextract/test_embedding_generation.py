#!/usr/bin/env python3
"""
Test script to verify embedding generation works correctly.
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

from core.openai_client import openai_client

def test_embedding_generation():
    """Test embedding generation with various inputs."""
    
    print("🧪 Testing OpenAI Embedding Generation")
    print("=" * 50)
    
    # Test 1: Check if OpenAI client is available
    print("\n1. Checking OpenAI client availability...")
    if not openai_client.is_available():
        print("❌ OpenAI client not available")
        print("Please check your OPENAI_API_KEY in settings")
        return False
    
    print("✅ OpenAI client is available")
    
    # Test 2: Test connection
    print("\n2. Testing OpenAI connection...")
    if not openai_client.test_connection():
        print("❌ OpenAI connection test failed")
        return False
    
    print("✅ OpenAI connection test passed")
    
    # Test 3: Generate embedding for simple text
    print("\n3. Testing embedding generation...")
    test_text = "This is a test document for embedding generation."
    
    try:
        embedding = openai_client.generate_embedding(test_text)
        
        if not embedding:
            print("❌ Embedding generation returned None")
            return False
        
        if len(embedding) == 0:
            print("❌ Embedding is empty")
            return False
        
        if len(embedding) != 1536:
            print(f"❌ Embedding dimension mismatch: expected 1536, got {len(embedding)}")
            return False
        
        print(f"✅ Embedding generated successfully (dimension: {len(embedding)})")
        print(f"   First 5 values: {embedding[:5]}")
        
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return False
    
    # Test 4: Test with empty text
    print("\n4. Testing with empty text...")
    try:
        empty_embedding = openai_client.generate_embedding("")
        if empty_embedding is None:
            print("✅ Empty text handled correctly (returned None)")
        else:
            print(f"⚠️ Empty text returned embedding: {len(empty_embedding) if empty_embedding else 0} dimensions")
    except Exception as e:
        print(f"✅ Empty text handled correctly (exception: {e})")
    
    # Test 5: Test with very long text
    print("\n5. Testing with long text...")
    long_text = "This is a very long text. " * 1000  # ~25,000 characters
    
    try:
        long_embedding = openai_client.generate_embedding(long_text)
        
        if not long_embedding:
            print("❌ Long text embedding generation returned None")
            return False
        
        if len(long_embedding) != 1536:
            print(f"❌ Long text embedding dimension mismatch: expected 1536, got {len(long_embedding)}")
            return False
        
        print(f"✅ Long text embedding generated successfully (dimension: {len(long_embedding)})")
        
    except Exception as e:
        print(f"❌ Long text embedding generation failed: {e}")
        return False
    
    print("\n🎉 All embedding tests passed!")
    return True

if __name__ == "__main__":
    success = test_embedding_generation()
    
    if success:
        print("\n✅ Embedding generation is working correctly.")
        print("You should be able to upload documents now.")
    else:
        print("\n❌ Embedding generation has issues.")
        print("Please check your OpenAI API key and configuration.")
