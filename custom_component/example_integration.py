"""
Example Integration: LangExtract Component with Dockling Chunker

This script demonstrates how to integrate the LangExtract custom component
with dockling chunker output for document processing.
"""

from langextract_component import (
    LangExtractComponent,
    ProcessingOptions,
    create_langextract_component,
    process_dockling_chunks,
    get_default_processing_options,
    get_recommended_schema_combinations
)
import json
import time


def simulate_dockling_chunker_output():
    """
    Simulate the output format that would come from dockling chunker.
    In a real scenario, this would be the actual output from your chunker.
    """
    return {
        "chunks": [
            {
                "text": "Invoice #INV-2024-001\nCustomer: John Doe\nAmount: $1,250.00\nDue Date: 2024-02-15\nStatus: Open",
                "document_id": "doc_001",
                "chunk_id": "chunk_001",
                "metadata": {"page": 1, "section": "header"}
            },
            {
                "text": "Line Items:\n1. Product A - Qty: 2 - Price: $500.00\n2. Product B - Qty: 1 - Price: $250.00\nTax: $125.00",
                "document_id": "doc_001",
                "chunk_id": "chunk_002",
                "metadata": {"page": 1, "section": "line_items"}
            },
            {
                "text": "Support Ticket #TKT-2024-001\nCustomer: Jane Smith\nIssue: Product not working\nUrgency: High\nSentiment: Negative",
                "document_id": "doc_002",
                "chunk_id": "chunk_003",
                "metadata": {"page": 1, "section": "ticket_header"}
            }
        ]
    }


def process_with_langextract():
    """Demonstrate processing dockling chunks with LangExtract."""
    
    print("🚀 LangExtract Component Integration Example")
    print("=" * 50)
    
    # Create component instance
    component = create_langextract_component("https://langextract.ai-did-it.eu")
    
    # Test connection
    print("\n📡 Testing API connection...")
    connection_status = component.test_connection()
    print(f"Status: {connection_status['status']}")
    print(f"API Accessible: {connection_status['api_accessible']}")
    
    if not connection_status['api_accessible']:
        print("❌ Cannot proceed without API access")
        return
    
    # Get available schemas
    print("\n📋 Available schemas:")
    schema_info = component.get_schema_info()
    for schema, description in schema_info['descriptions'].items():
        print(f"  • {schema}: {description}")
    
    # Simulate dockling chunker output
    print("\n📄 Simulating dockling chunker output...")
    chunker_output = simulate_dockling_chunker_output()
    
    # Extract data from chunker output
    text_chunks = [chunk['text'] for chunk in chunker_output['chunks']]
    document_ids = [chunk['document_id'] for chunk in chunker_output['chunks']]
    chunk_ids = [chunk['chunk_id'] for chunk in chunker_output['chunks']]
    metadata_list = [chunk.get('metadata', {}) for chunk in chunker_output['chunks']]
    
    print(f"Extracted {len(text_chunks)} chunks for processing")
    
    # Process chunks with different schema combinations
    print("\n🔍 Processing chunks with different schemas...")
    
    # Example 1: Process invoice-related chunks
    invoice_chunks = [0, 1]  # First two chunks are invoice-related
    print(f"\n📊 Processing invoice chunks (chunks {invoice_chunks}) with 'invoice' schema...")
    
    try:
        invoice_results = component.process_text_chunks(
            text_chunks=[text_chunks[i] for i in invoice_chunks],
            document_ids=[document_ids[i] for i in invoice_chunks],
            chunk_ids=[chunk_ids[i] for i in invoice_chunks],
            schemas=["invoice"],
            options=get_default_processing_options(),
            metadata=[metadata_list[i] for i in invoice_chunks]
        )
        
        print(f"✅ Successfully processed {len(invoice_results)} invoice chunks")
        for result in invoice_results:
            print(f"  - Chunk {result.chunk_id}: {len(result.extracted_data.get('entities', []))} entities extracted")
            
    except Exception as e:
        print(f"❌ Error processing invoice chunks: {e}")
    
    # Example 2: Process support case chunk
    support_chunk = 2  # Third chunk is support-related
    print(f"\n🎫 Processing support case chunk (chunk {support_chunk}) with 'support_case' schema...")
    
    try:
        support_result = component.process_single_chunk(
            text=text_chunks[support_chunk],
            document_id=document_ids[support_chunk],
            chunk_id=chunk_ids[support_chunk],
            schemas=["support_case"],
            options=ProcessingOptions(
                extract_entities=True,
                extract_categories=True,
                confidence_threshold=0.8
            ),
            metadata=metadata_list[support_chunk]
        )
        
        if support_result:
            print(f"✅ Successfully processed support case chunk")
            print(f"  - Intent detected: {support_result.extracted_data.get('entities', [])}")
            print(f"  - Processing time: {support_result.processing_time:.2f}s")
            
    except Exception as e:
        print(f"❌ Error processing support case chunk: {e}")
    
    # Example 3: Process all chunks with multiple schemas
    print(f"\n🔄 Processing all chunks with multiple schemas...")
    
    try:
        all_results = component.process_text_chunks(
            text_chunks=text_chunks,
            document_ids=document_ids,
            chunk_ids=chunk_ids,
            schemas=["invoice", "support_case"],
            options=ProcessingOptions(
                extract_entities=True,
                extract_categories=True,
                confidence_threshold=0.7
            ),
            metadata=metadata_list
        )
        
        print(f"✅ Successfully processed all {len(all_results)} chunks with multiple schemas")
        
        # Show summary
        summary = component.get_processing_summary()
        print(f"\n📈 Processing Summary:")
        print(f"  - Total chunks processed: {summary['total_chunks_processed']}")
        print(f"  - Total operations: {summary['total_operations']}")
        print(f"  - Schemas used: {', '.join(summary['unique_schemas_used'])}")
        
    except Exception as e:
        print(f"❌ Error processing all chunks: {e}")
    
    # Show recommended schema combinations
    print(f"\n💡 Recommended schema combinations:")
    for combo in get_recommended_schema_combinations():
        print(f"  • {', '.join(combo)}")


def demonstrate_convenience_functions():
    """Demonstrate the convenience functions for direct dockling integration."""
    
    print("\n\n🔧 Convenience Functions Demo")
    print("=" * 40)
    
    # Simulate chunker output
    chunker_output = simulate_dockling_chunker_output()
    
    # Extract data
    text_chunks = [chunk['text'] for chunk in chunker_output['chunks']]
    document_ids = [chunk['document_id'] for chunk in chunker_output['chunks']]
    chunk_ids = [chunk['chunk_id'] for chunk in chunker_output['chunks']]
    
    print("📝 Using process_dockling_chunks() convenience function...")
    
    try:
        results = process_dockling_chunks(
            text_chunks=text_chunks,
            document_ids=document_ids,
            chunk_ids=chunk_ids,
            schemas=["invoice", "support_case"],
            api_url="https://langextract.ai-did-it.eu"
        )
        
        print(f"✅ Convenience function processed {len(results)} chunks successfully")
        
    except Exception as e:
        print(f"❌ Convenience function error: {e}")


def main():
    """Main function to run the integration example."""
    
    try:
        # Run the main integration example
        process_with_langextract()
        
        # Run convenience functions demo
        demonstrate_convenience_functions()
        
        print("\n🎉 Integration example completed successfully!")
        print("\nTo use this component in your application:")
        print("1. Import the component: from langextract_component import LangExtractComponent")
        print("2. Create instance: component = LangExtractComponent('https://langextract.ai-did-it.eu')")
        print("3. Process chunks: results = component.process_text_chunks(text_chunks, doc_ids, chunk_ids, schemas)")
        print("4. Or use convenience function: results = process_dockling_chunks(text_chunks, doc_ids, chunk_ids, schemas)")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Example interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
