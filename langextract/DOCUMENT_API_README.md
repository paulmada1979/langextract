# Document Processing API Module

This module provides a complete document processing and AI chat system that integrates with the existing LangExtract infrastructure. It allows users to upload documents, extract metadata using LangExtract schemas, create embeddings, and interact with documents through an AI chat interface.

## Features

### 🚀 Core Functionality

- **Document Upload**: Support for PDF, DOCX, DOC, MD, and TXT files
- **Document Processing**: Uses Docling for content extraction with optimized settings
- **Intelligent Chunking**: Optimized chunking strategy for large documents
- **Metadata Extraction**: Integrates with LangExtract schemas for structured data extraction
- **Vector Embeddings**: Generates and stores embeddings for semantic search
- **AI Chat Interface**: Interactive chat with documents using OpenAI

### 📊 Database Schema

- **documents**: Track uploaded files and processing status
- **processed_embeddings**: Store document chunks with embeddings and metadata
- **chat_sessions**: Manage AI chat sessions
- **chat_messages**: Store chat history and context

### 🎯 Performance Optimizations

- **Async Processing**: Non-blocking document processing pipeline
- **Batch Operations**: Efficient batch storage of embeddings
- **Optimized Chunking**: Smart chunking with overlap and size optimization
- **Vector Search**: Fast similarity search using pgvector

## Installation

### 1. Database Setup

Run the SQL migration to create the required tables:

```sql
-- Run this in your Supabase SQL editor
\i db/migrations/003_create_document_processing_tables.sql
```

### 2. Install Dependencies

```bash
pip install -r document_requirements.txt
```

### 3. Environment Variables

Ensure these environment variables are set:

```bash
# Existing LangExtract variables
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Optional: File upload settings
MAX_FILE_SIZE=52428800  # 50MB default
UPLOAD_DIR=uploads      # Directory for file storage
```

## API Endpoints

### Document Management

#### Upload Document

```http
POST /api/document/documents/upload/
Content-Type: multipart/form-data

{
  "file": <file_data>,
  "userId": "123e4567-e89b-12d3-a456-426614174000",
  "schemas": ["invoice", "support_case", "refund_case"]
}
```

#### List Documents

```http
GET /api/document/documents/
```

#### Get Document Details

```http
GET /api/document/documents/{document_id}/
```

#### Get Document Status

```http
GET /api/document/documents/{document_id}/status/
```

#### Delete Document

```http
DELETE /api/document/documents/{document_id}/delete/
```

#### Search Documents

```http
GET /api/document/documents/search/?query=your_search_query&document_ids=uuid1,uuid2
```

#### Get System Stats

```http
GET /api/document/documents/stats/
```

### Chat Management

#### Create Chat Session

```http
POST /api/document/chat/sessions/
{
  "session_name": "My Chat Session",
  "document_ids": ["uuid1", "uuid2"]
}
```

#### List Chat Sessions

```http
GET /api/document/chat/sessions/list/
```

#### Get Chat Session

```http
GET /api/document/chat/sessions/{session_id}/
```

#### Send Message

```http
POST /api/document/chat/message/
{
  "message": "What is this document about?",
  "userId": "123e4567-e89b-12d3-a456-426614174000",
  "document_ids": ["uuid1", "uuid2"],  // Optional: if not provided, searches all user's documents
  "include_sources": true,
  "max_tokens": 1000,
  "temperature": 0.7
}
```

#### Delete Chat Session

```http
DELETE /api/document/chat/sessions/{session_id}/delete/
```

### Web Interface

#### Chat Interface

```http
GET /api/document/chat/
```

## Usage Examples

### Python Client Example

```python
import requests
import json

# Upload a document
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    data = {'schemas': json.dumps(['invoice', 'support_case'])}
    response = requests.post(
        'http://localhost:8000/api/document/documents/upload/',
        files=files,
        data=data
    )

    if response.status_code == 201:
        result = response.json()
        document_id = result['data']['document_id']
        print(f"Document uploaded: {document_id}")

# Chat with the document
chat_response = requests.post(
    'http://localhost:8000/api/document/chat/message/',
    json={
        'message': 'What is the total amount in this invoice?',
        'document_ids': [document_id],
        'include_sources': True
    }
)

if chat_response.status_code == 200:
    result = chat_response.json()
    print(f"AI Response: {result['data']['message']}")
    print(f"Sources: {len(result['data']['sources'])} chunks referenced")
```

### JavaScript/Web Example

```javascript
// Upload document
const formData = new FormData();
formData.append("file", fileInput.files[0]);
formData.append("schemas", JSON.stringify(["invoice", "support_case"]));

const uploadResponse = await fetch("/api/document/documents/upload/", {
  method: "POST",
  body: formData,
});

const uploadResult = await uploadResponse.json();
const documentId = uploadResult.data.document_id;

// Chat with document
const chatResponse = await fetch("/api/document/chat/message/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    message: "What is this document about?",
    document_ids: [documentId],
    include_sources: true,
  }),
});

const chatResult = await chatResponse.json();
console.log("AI Response:", chatResult.data.message);
```

## Architecture

### Document Processing Pipeline

1. **File Upload**: Validate file type and size
2. **Storage**: Store file to disk with unique ID
3. **Extraction**: Use Docling to extract text, tables, and images
4. **Chunking**: Split content into optimal chunks with overlap
5. **Metadata Extraction**: Apply LangExtract schemas to extract structured data
6. **Embedding Generation**: Create vector embeddings for semantic search
7. **Storage**: Store chunks and embeddings in database

### Chat Processing Pipeline

1. **Message Reception**: Receive user message and document context
2. **Query Embedding**: Generate embedding for user query
3. **Vector Search**: Find relevant document chunks using similarity search
4. **Context Preparation**: Prepare context from relevant chunks
5. **AI Generation**: Generate response using OpenAI with document context
6. **Response Storage**: Store both user message and AI response
7. **Source Attribution**: Return relevant source chunks for transparency

## Configuration

### Chunking Configuration

```python
# In document_processor/chunker.py
@dataclass
class ChunkConfig:
    max_chunk_size: int = 1000      # Maximum characters per chunk
    min_chunk_size: int = 200       # Minimum characters per chunk
    overlap_size: int = 100         # Overlap between chunks
    preserve_sentences: bool = True # Try to preserve sentence boundaries
    preserve_paragraphs: bool = True # Try to preserve paragraph boundaries
```

### Supported Schemas

The system supports all LangExtract schemas:

- `invoice` - Invoice processing
- `support_case` - Support ticket processing
- `refund_case` - Refund processing
- `contract_terms` - Contract analysis
- `sop_steps` - Standard operating procedures
- `price_list` - Price list processing
- `product_spec` - Product specifications
- `faq` - Frequently asked questions
- `policy` - Policy documents

## Performance Considerations

### Optimization Features

1. **Async Processing**: All I/O operations are asynchronous
2. **Batch Operations**: Database operations are batched for efficiency
3. **Smart Chunking**: Optimized chunk sizes for better processing
4. **Vector Indexing**: Efficient similarity search with pgvector
5. **Caching**: Embeddings are cached to avoid regeneration

### Scaling Recommendations

1. **Database**: Use connection pooling for Supabase
2. **File Storage**: Consider cloud storage (S3, GCS) for large files
3. **Processing**: Use background task queues (Celery) for large documents
4. **Caching**: Implement Redis for frequently accessed data
5. **Load Balancing**: Use multiple instances for high availability

## Error Handling

The system includes comprehensive error handling:

- **File Validation**: Size, type, and format validation
- **Processing Errors**: Graceful handling of extraction failures
- **Database Errors**: Connection and query error handling
- **API Errors**: Structured error responses with details
- **User Feedback**: Clear error messages and status updates

## Monitoring and Logging

### Logging Levels

- **INFO**: Document processing milestones
- **DEBUG**: Detailed processing information
- **WARNING**: Non-critical issues
- **ERROR**: Processing failures
- **CRITICAL**: System-level failures

### Metrics to Monitor

1. **Document Processing**: Upload success rate, processing time
2. **Chat Performance**: Response time, user satisfaction
3. **Database Performance**: Query time, connection pool usage
4. **System Resources**: CPU, memory, disk usage
5. **Error Rates**: Failed uploads, processing errors

## Security Considerations

1. **File Validation**: Strict file type and size validation
2. **Input Sanitization**: All user inputs are sanitized
3. **Access Control**: Implement authentication/authorization as needed
4. **Data Privacy**: Sensitive data handling and retention policies
5. **API Security**: Rate limiting and request validation

## Troubleshooting

### Common Issues

1. **File Upload Fails**: Check file size limits and supported formats
2. **Processing Stuck**: Check OpenAI API key and Supabase connection
3. **Chat Not Working**: Verify document processing completed successfully
4. **Slow Performance**: Check database indexes and connection pooling
5. **Memory Issues**: Monitor chunk sizes and batch processing

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('document_processor').setLevel(logging.DEBUG)
```

## Contributing

1. Follow the existing code structure
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure backward compatibility
5. Follow async/await patterns for I/O operations

## License

This module is part of the LangExtract project and follows the same licensing terms.
