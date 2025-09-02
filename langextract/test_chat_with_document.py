#!/usr/bin/env python3
"""
Test chat functionality with the uploaded document.
"""

import requests
import json

def test_chat_with_document():
    """Test chat API with the uploaded document."""
    
    # API endpoint (from inside Docker container, use the service name)
    url = "http://web:8000/api/document/chat/message/"
    
    # User ID
    user_id = "2e4d6dc7-1050-425b-a9e9-f717aed867de"
    
    # Test questions about the uploaded PDF
    test_questions = [
        "What is this document about?",
        "Is this an invoice?",
        "What information can you find in this document?",
        "Can you summarize the content?",
        "What are the key details in this document?"
    ]
    
    print("💬 Testing Chat with Uploaded Document")
    print("=" * 50)
    print(f"User ID: {user_id}")
    print(f"Document ID: 09545519-8bde-401a-b0a6-3a35469aa523")
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Question: {question}")
        
        # Prepare the request
        data = {
            'message': question,
            'userId': user_id
        }
        
        try:
            response = requests.post(url, json=data)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    data = result.get('data', {})
                    message = data.get('message', '')
                    chunks_searched = data.get('metadata', {}).get('chunks_searched', 0)
                    chunks_used = data.get('metadata', {}).get('chunks_used', 0)
                    sources = data.get('sources', [])
                    
                    print(f"   ✅ Response: {message[:150]}...")
                    print(f"   📊 Chunks searched: {chunks_searched}, used: {chunks_used}")
                    print(f"   📚 Sources found: {len(sources)}")
                    
                    if sources:
                        print(f"   📄 Source preview: {sources[0].get('content', '')[:100]}...")
                else:
                    print(f"   ❌ API Error: {result.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Request Error: {e}")

if __name__ == "__main__":
    test_chat_with_document()
