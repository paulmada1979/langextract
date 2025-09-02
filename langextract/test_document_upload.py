#!/usr/bin/env python3
"""
Test script to upload a document and verify the system works.
"""

import requests
import os
from pathlib import Path

def test_document_upload():
    """Test uploading a document."""
    
    # API endpoint
    url = "http://localhost:8001/api/document/documents/upload/"
    
    # User ID
    user_id = "2e4d6dc7-1050-425b-a9e9-f717aed867de"
    
    # Create a simple test document
    test_content = """
    This is a test invoice document.
    
    Invoice Number: INV-001
    Date: 2025-09-02
    Customer: Test Customer
    Amount: $100.00
    
    This document contains information about a sample invoice.
    It should be processed and made searchable through the chat API.
    """
    
    # Create test file
    test_file_path = "test_invoice.txt"
    with open(test_file_path, "w") as f:
        f.write(test_content)
    
    try:
        # Prepare the request
        files = {
            'file': ('test_invoice.txt', open(test_file_path, 'rb'), 'text/plain')
        }
        
        data = {
            'userId': user_id
        }
        
        print(f"📤 Uploading test document...")
        print(f"   User ID: {user_id}")
        print(f"   File: {test_file_path}")
        
        # Make the request
        response = requests.post(url, files=files, data=data)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Document uploaded successfully!")
            print("   Now you can test the chat API with questions about the invoice.")
        else:
            print("❌ Upload failed")
            
    except Exception as e:
        print(f"❌ Error uploading document: {e}")
    
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            print(f"🧹 Cleaned up test file: {test_file_path}")

if __name__ == "__main__":
    test_document_upload()
