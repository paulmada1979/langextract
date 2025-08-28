# LangExtract Custom Component

A comprehensive Python component for integrating with the deployed LangExtract application at `https://langextract.ai-did-it.eu/api/process/`. This component provides seamless integration with dockling chunker and supports all available schemas.

## Features

- 🚀 **Direct API Integration**: Communicates with deployed LangExtract application
- 📄 **Schema Support**: All 9 available schemas supported
- 🔗 **Dockling Chunker Integration**: Direct hook for chunker output
- ⚙️ **Configurable Options**: Customizable processing parameters
- 🔄 **Batch Processing**: Process multiple chunks simultaneously
- 📊 **Comprehensive Results**: Rich extraction results with metadata
- 🛡️ **Error Handling**: Robust error handling with retry logic
- 📈 **Processing History**: Track and monitor processing operations

## Available Schemas

| Schema           | Description                                      | Use Case                     |
| ---------------- | ------------------------------------------------ | ---------------------------- |
| `support_case`   | Support/inquiry email or ticket processing       | Customer service, help desk  |
| `refund_case`    | Refund case processing with retail domain        | E-commerce, customer support |
| `invoice`        | Invoice document processing and data extraction  | Financial documents, billing |
| `contract_terms` | Contract terms and conditions extraction         | Legal documents, agreements  |
| `sop_steps`      | Standard Operating Procedure steps extraction    | Process documentation        |
| `price_list`     | Price list and pricing information extraction    | Product catalogs, pricing    |
| `product_spec`   | Product specification extraction                 | Product documentation        |
| `faq`            | Frequently Asked Questions processing            | Knowledge base, help content |
| `policy`         | Policy document processing and clause extraction | Legal, compliance documents  |

## Installation

1. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Import the Component**:
   ```python
   from langextract_component import LangExtractComponent, ProcessingOptions
   ```

## Quick Start

### Basic Usage

```python
from langextract_component import create_langextract_component

# Create component instance
component = create_langextract_component("https://langextract.ai-did-it.eu")

# Test connection
status = component.test_connection()
print(f"API Status: {status['status']}")

# Get available schemas
schemas = component.get_schema_info()
print(f"Available schemas: {schemas['schemas']}")
```

### Process Single Chunk

```python
# Process a single text chunk
result = component.process_single_chunk(
    text="Invoice #INV-001\nCustomer: John Doe\nAmount: $100.00",
    document_id="doc_001",
    chunk_id="chunk_001",
    schemas=["invoice"]
)

print(f"Extracted entities: {result.extracted_data['entities']}")
```

### Process Multiple Chunks (Dockling Integration)

```python
# Process multiple chunks from dockling chunker
text_chunks = ["chunk1 text", "chunk2 text", "chunk3 text"]
document_ids = ["doc_001", "doc_001", "doc_002"]
chunk_ids = ["chunk_001", "chunk_002", "chunk_003"]

results = component.process_text_chunks(
    text_chunks=text_chunks,
    document_ids=document_ids,
    chunk_ids=chunk_ids,
    schemas=["invoice", "support_case"]
)

for result in results:
    print(f"Chunk {result.chunk_id}: {len(result.extracted_data['entities'])} entities")
```

## Advanced Usage

### Custom Processing Options

```python
from langextract_component import ProcessingOptions

# Configure processing options
options = ProcessingOptions(
    extract_entities=True,
    extract_categories=True,
    confidence_threshold=0.8
)

# Process with custom options
results = component.process_text_chunks(
    text_chunks=text_chunks,
    document_ids=document_ids,
    chunk_ids=chunk_ids,
    schemas=["invoice"],
    options=options
)
```

### Convenience Functions

```python
from langextract_component import process_dockling_chunks

# Direct processing of dockling chunks
results = process_dockling_chunks(
    text_chunks=text_chunks,
    document_ids=document_ids,
    chunk_ids=chunk_ids,
    schemas=["invoice", "support_case"],
    api_url="https://langextract.ai-did-it.eu"
)
```

### Processing History and Monitoring

```python
# Get processing summary
summary = component.get_processing_summary()
print(f"Total chunks processed: {summary['total_chunks_processed']}")
print(f"Schemas used: {summary['unique_schemas_used']}")

# Get recent operations
recent = summary['recent_operations']
for op in recent:
    print(f"Processed {op['chunks_processed']} chunks with schemas: {op['schemas_used']}")
```

## Schema Combinations

### Recommended Combinations

```python
from langextract_component import get_recommended_schema_combinations

combinations = get_recommended_schema_combinations()
for combo in combinations:
    print(f"Use case: {', '.join(combo)}")
```

**Common Use Cases:**

- **Invoice Processing**: `["invoice"]`
- **Customer Support**: `["support_case"]`
- **E-commerce**: `["refund_case", "support_case"]`
- **Product Management**: `["product_spec", "price_list"]`
- **Legal Documents**: `["contract_terms", "policy"]`

## API Response Structure

The component returns structured data with the following format:

```python
@dataclass
class ProcessingResult:
    chunk_id: str                    # Unique chunk identifier
    document_id: str                 # Document identifier
    original_text: str               # Original text content
    extracted_data: Dict[str, Any]  # Extracted entities, categories, etc.
    embeddings: Dict[str, Any]      # Text embeddings and vectors
    metadata: Dict[str, Any]        # Processing metadata
    processing_time: float           # Processing time in seconds
    schemas_applied: List[str]      # Schemas used for processing
```

### Extracted Data Structure

```python
extracted_data = {
    "entities": [
        {"text": "INV-001", "label": "invoice_no", "confidence": 0.95}
    ],
    "categories": [
        {"name": "financial_document", "confidence": 0.88}
    ],
    "key_phrases": ["invoice", "customer", "amount"],
    "schema_matches": {
        "invoice": {"confidence": 0.92, "fields_matched": ["invoice_no", "customer"]}
    }
}
```

## Error Handling

The component includes comprehensive error handling:

```python
try:
    results = component.process_text_chunks(
        text_chunks=text_chunks,
        document_ids=document_ids,
        chunk_ids=chunk_ids,
        schemas=["invoice"]
    )
except ValueError as e:
    print(f"Validation error: {e}")
except RuntimeError as e:
    print(f"API communication error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Configuration

### Environment Variables

```bash
# Optional: Override default API URL
export LANGEXTRACT_API_URL="https://your-custom-domain.com"

# Optional: Set timeout
export LANGEXTRACT_TIMEOUT="60"
```

### Custom Configuration

```python
# Create component with custom settings
component = LangExtractComponent(
    api_url="https://your-custom-domain.com"
)

# Test with custom timeout
client = component.client
client.timeout = 60
```

## Performance Considerations

- **Batch Processing**: Process multiple chunks in single API call for better performance
- **Schema Selection**: Use only necessary schemas to reduce processing time
- **Confidence Thresholds**: Adjust confidence thresholds based on your accuracy requirements
- **Retry Logic**: Built-in retry logic handles temporary API issues

## Monitoring and Debugging

### Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Component logs all operations
logger = logging.getLogger('langextract_component')
```

### Health Checks

```python
# Check API health
is_healthy = component.client.health_check()
if not is_healthy:
    print("API is not responding")
```

## Examples

### Complete Integration Example

```python
from langextract_component import create_langextract_component, ProcessingOptions

def process_documents_with_langextract(chunks_data):
    """Process document chunks using LangExtract."""

    # Create component
    component = create_langextract_component()

    # Extract data from chunks
    text_chunks = [chunk['text'] for chunk in chunks_data]
    document_ids = [chunk['doc_id'] for chunk in chunks_data]
    chunk_ids = [chunk['chunk_id'] for chunk in chunks_data]

    # Process with appropriate schemas
    results = component.process_text_chunks(
        text_chunks=text_chunks,
        document_ids=document_ids,
        chunk_ids=chunk_ids,
        schemas=["invoice", "support_case"],
        options=ProcessingOptions(confidence_threshold=0.8)
    )

    return results

# Usage
chunks = [
    {"text": "Invoice content...", "doc_id": "doc1", "chunk_id": "chunk1"},
    {"text": "Support ticket...", "doc_id": "doc2", "chunk_id": "chunk2"}
]

results = process_documents_with_langextract(chunks)
```

## Troubleshooting

### Common Issues

1. **API Connection Failed**

   - Check if the API URL is correct
   - Verify network connectivity
   - Check if the service is running

2. **Invalid Schema Error**

   - Use `component.get_schema_info()` to see available schemas
   - Check schema names for typos

3. **Processing Timeout**

   - Increase timeout value
   - Reduce batch size
   - Check API performance

4. **Validation Errors**
   - Ensure all required fields are provided
   - Check data types and formats
   - Verify chunk text length (max 32,000 characters)

### Debug Mode

```python
# Enable debug mode for detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test individual components
component = create_langextract_component()
status = component.test_connection()
print(f"Connection status: {status}")
```

## Support

For issues or questions:

1. Check the error messages and logs
2. Verify API connectivity and health
3. Review schema configurations
4. Check input data format and validation

## License

This component is provided as-is for integration with the LangExtract application.
