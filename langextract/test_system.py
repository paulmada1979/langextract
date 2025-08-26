#!/usr/bin/env python3
"""
Simple test script to verify LangExtract system components.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'langextract.settings')
django.setup()

from core.schema_loader import schema_loader
from core.openai_client import openai_client
from core.processor import document_processor


def test_schema_loading():
    """Test schema loading functionality."""
    print("Testing schema loading...")
    
    try:
        schemas = schema_loader.list_schemas()
        vocabularies = schema_loader.list_vocabularies()
        
        print(f"✓ Loaded {len(schemas)} schemas: {schemas}")
        print(f"✓ Loaded {len(vocabularies)} vocabularies: {vocabularies}")
        
        # Test getting a specific schema
        if schemas:
            test_schema = schema_loader.get_schema(schemas[0])
            print(f"✓ Successfully loaded schema: {schemas[0]}")
        
        return True
    except Exception as e:
        print(f"✗ Schema loading failed: {e}")
        return False


def test_openai_connection():
    """Test OpenAI API connection."""
    print("\nTesting OpenAI connection...")
    
    try:
        # Check if API key is configured
        if not openai_client.api_key:
            print("✗ OpenAI API key not configured")
            return False
        
        # Test connection
        if openai_client.test_connection():
            print("✓ OpenAI connection successful")
            print(f"✓ Model: {openai_client.model}")
            print(f"✓ Max tokens: {openai_client.max_tokens}")
            return True
        else:
            print("✗ OpenAI connection failed")
            return False
    except Exception as e:
        print(f"✗ OpenAI test failed: {e}")
        return False


def test_text_processing():
    """Test text processing functionality."""
    print("\nTesting text processing...")
    
    try:
        test_text = "This is a test contract between Company A and Company B, effective from 2024-01-01."
        test_schemas = ['contract_terms']
        test_options = {'extract_entities': True, 'extract_categories': True}
        
        result = document_processor.schema_extractor.extract_from_chunk(
            test_text, test_schemas, test_options
        )
        
        if result:
            print("✓ Text processing successful")
            print(f"✓ Processing time: {result['metadata']['processing_time']}s")
            print(f"✓ Schemas applied: {result['metadata']['schemas_applied']}")
            return True
        else:
            print("✗ Text processing failed")
            return False
    except Exception as e:
        print(f"✗ Text processing test failed: {e}")
        return False


def test_system_integration():
    """Test the complete system integration."""
    print("\nTesting system integration...")
    
    try:
        test_results = document_processor.test_system()
        
        print("System test results:")
        for component, status in test_results.items():
            status_symbol = "✓" if status else "✗"
            print(f"  {status_symbol} {component}: {'OK' if status else 'FAILED'}")
        
        overall_status = all(test_results.values())
        if overall_status:
            print("✓ All system components are working")
        else:
            print("✗ Some system components failed")
        
        return overall_status
    except Exception as e:
        print(f"✗ System integration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("LangExtract System Test")
    print("=" * 50)
    
    tests = [
        ("Schema Loading", test_schema_loading),
        ("OpenAI Connection", test_openai_connection),
        ("Text Processing", test_text_processing),
        ("System Integration", test_system_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        return 0
    else:
        print("❌ Some tests failed. Please check the configuration.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
