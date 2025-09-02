#!/usr/bin/env python3
"""
Test script to verify chat works after document upload.
"""

import requests
import json

def test_chat_after_upload():
    """Test chat API after document upload."""
    
    # API endpoint
    url = "http://localhost:8001/api/document/chat/message/"
    
    # User ID
    user_id = "2e4d6dc7-1050-425b-a9e9-f717aed867de"
    
    # Test questions
    test_questions = [
        "What is the invoice number?",
        "What is the amount?",
        "Who is the customer?",
        "Is this an invoice document?"
    ]
    
    print("💬 Testing Chat API")
    print("=" * 50)
    
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
                    
                    print(f"   ✅ Response: {message[:100]}...")
                    print(f"   📊 Chunks searched: {chunks_searched}, used: {chunks_used}")
                else:
                    print(f"   ❌ API Error: {result.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Request Error: {e}")

if __name__ == "__main__":
    test_chat_after_upload()
