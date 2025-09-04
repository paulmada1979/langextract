#!/usr/bin/env python3
"""
Test script to verify PDF processing fix with docling support.
"""

import requests
import json
import os
from pathlib import Path

def test_pdf_upload_with_docling():
    """Test PDF upload with docling enabled."""
    
    # Test configuration
    base_url = "http://localhost:8001"  # Adjust if needed
    upload_url = f"{base_url}/api/document/documents/upload/"
    
    # Create a simple test PDF content (this is just a placeholder)
    # In a real test, you would use an actual PDF file
    test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF Content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"
    
    # Prepare form data
    files = {
        'file': ('test.pdf', test_pdf_content, 'application/pdf')
    }
    
    data = {
        'userId': 'test-user-123',
        'enable_docling': 'true',
        'processing_options': json.dumps({
            'extractText': True,
            'analyzeStructure': True,
            'enableDocling': True,
            'fileType': 'pdf',
            'autoDetectSchema': True,
            'skipSchemaValidation': True
        })
    }
    
    print("Testing PDF upload with docling enabled...")
    print(f"Upload URL: {upload_url}")
    print(f"Data: {data}")
    
    try:
        response = requests.post(upload_url, files=files, data=data, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Check if the content was properly extracted
            if 'data' in result and 'chunks' in result['data']:
                chunks = result['data']['chunks']
                if chunks:
                    first_chunk = chunks[0]
                    content = first_chunk.get('content', '')
                    if '[File type pdf not supported without docling]' in content:
                        print("❌ PDF processing still shows docling error - fix may not be working")
                    else:
                        print("✅ PDF content was extracted successfully!")
                        print(f"First chunk content preview: {content[:200]}...")
                else:
                    print("⚠️  No chunks found in response")
            else:
                print("⚠️  Unexpected response structure")
        else:
            print(f"❌ Upload failed with status {response.status_code}")
            print(f"Error response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_pdf_upload_without_docling():
    """Test PDF upload without docling to verify fallback behavior."""
    
    base_url = "http://localhost:8001"
    upload_url = f"{base_url}/api/document/documents/upload/"
    
    # Create a simple test PDF content
    test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF Content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"
    
    files = {
        'file': ('test.pdf', test_pdf_content, 'application/pdf')
    }
    
    data = {
        'userId': 'test-user-123',
        'enable_docling': 'false',  # Disable docling
        'processing_options': json.dumps({
            'extractText': True,
            'analyzeStructure': True,
            'enableDocling': False,
            'fileType': 'pdf',
            'autoDetectSchema': True,
            'skipSchemaValidation': True
        })
    }
    
    print("\nTesting PDF upload without docling (should show error message)...")
    print(f"Upload URL: {upload_url}")
    print(f"Data: {data}")
    
    try:
        response = requests.post(upload_url, files=files, data=data, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Check if the content shows the expected error message
            if 'data' in result and 'chunks' in result['data']:
                chunks = result['data']['chunks']
                if chunks:
                    first_chunk = chunks[0]
                    content = first_chunk.get('content', '')
                    if '[File type pdf not supported without docling]' in content:
                        print("✅ Correctly shows docling error message when docling is disabled")
                    else:
                        print("⚠️  Unexpected content when docling is disabled")
                        print(f"Content: {content}")
                else:
                    print("⚠️  No chunks found in response")
            else:
                print("⚠️  Unexpected response structure")
        else:
            print(f"❌ Upload failed with status {response.status_code}")
            print(f"Error response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🧪 Testing PDF Processing Fix")
    print("=" * 50)
    
    # Test with docling enabled
    test_pdf_upload_with_docling()
    
    # Test with docling disabled
    test_pdf_upload_without_docling()
    
    print("\n" + "=" * 50)
    print("Test completed!")
