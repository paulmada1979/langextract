#!/usr/bin/env python3
"""
Test script to demonstrate improved schema extraction.
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

from core.schema_extractor import schema_extractor


def test_contract_extraction():
    """Test contract terms extraction."""
    print("Testing Contract Terms Extraction")
    print("=" * 40)
    
    test_text = """
    CONTRACT AGREEMENT
    
    This agreement is made between ABC Corporation and XYZ Industries, 
    effective from January 1, 2024, for a term of 12 months with automatic renewal.
    
    Payment terms: Net 30 days from invoice date.
    Termination clause: Either party may terminate with 30 days written notice.
    Governing law: Delaware state law.
    
    Parties agree to the terms above.
    """
    
    schemas = ['contract_terms']
    options = {'extract_entities': True, 'extract_categories': True, 'confidence_threshold': 0.5}
    
    result = schema_extractor.extract_from_chunk(test_text, schemas, options)
    
    if result and 'extracted_data' in result:
        print(f"Processing time: {result['metadata']['processing_time']}s")
        print(f"Schemas applied: {result['metadata']['schemas_applied']}")
        
        schema_matches = result['extracted_data']['schema_matches']
        if 'contract_terms' in schema_matches:
            print("\nExtracted Contract Terms:")
            for field, value in schema_matches['contract_terms'].items():
                print(f"  {field}: {value}")
        else:
            print("No contract terms extracted")
        
        print(f"\nEntities: {len(result['extracted_data']['entities'])}")
        print(f"Categories: {len(result['extracted_data']['categories'])}")
        print(f"Key phrases: {result['extracted_data']['key_phrases']}")
    
    return result


def test_invoice_extraction():
    """Test invoice extraction."""
    print("\n\nTesting Invoice Extraction")
    print("=" * 40)
    
    test_text = """
    INVOICE
    
    Invoice Number: INV-2024-001
    Customer: ABC Corporation
    Issue Date: January 15, 2024
    Due Date: February 14, 2024
    
    Subtotal: $1,000.00
    Tax: $100.00
    Grand Total: $1,100.00
    
    Status: Open
    Payment Terms: Net 30
    """
    
    schemas = ['invoice']
    options = {'extract_entities': True, 'extract_categories': True, 'confidence_threshold': 0.5}
    
    result = schema_extractor.extract_from_chunk(test_text, schemas, options)
    
    if result and 'extracted_data' in result:
        print(f"Processing time: {result['metadata']['processing_time']}s")
        print(f"Schemas applied: {result['metadata']['schemas_applied']}")
        
        schema_matches = result['extracted_data']['schema_matches']
        if 'invoice' in schema_matches:
            print("\nExtracted Invoice Data:")
            for field, value in schema_matches['invoice'].items():
                print(f"  {field}: {value}")
        else:
            print("No invoice data extracted")
        
        print(f"\nEntities: {len(result['extracted_data']['entities'])}")
        print(f"Categories: {len(result['extracted_data']['categories'])}")
        print(f"Key phrases: {result['extracted_data']['key_phrases']}")
    
    return result


def main():
    """Run all extraction tests."""
    print("LangExtract Schema Extraction Test")
    print("=" * 50)
    
    # Test contract extraction
    contract_result = test_contract_extraction()
    
    # Test invoice extraction
    invoice_result = test_invoice_extraction()
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Contract extraction: {'SUCCESS' if contract_result and 'contract_terms' in contract_result['extracted_data']['schema_matches'] else 'FAILED'}")
    print(f"Invoice extraction: {'SUCCESS' if invoice_result and 'invoice' in invoice_result['extracted_data']['schema_matches'] else 'FAILED'}")


if __name__ == '__main__':
    main()
