# Vector Storage Integration for Langextract

This document explains how to integrate Supabase vector database storage with your langextract service to store and search document embeddings.

## Overview

The vector storage integration allows you to:
- Store document embeddings in Supabase with pgvector support
- Perform similarity searches using vector embeddings
- Maintain all your existing relational data without interference
- Scale your embedding storage independently

## Prerequisites

1. **Supabase Project**: You need a Supabase project with pgvector extension enabled
2. **Environment Variables**: Configure your Supabase credentials
3. **Dependencies**: Install the required Python packages

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The following new dependencies have been added:
- `supabase==2.0.2` - Supabase Python client
- `pgvector==0.2.3` - PostgreSQL vector extension support
- `psycopg2-binary==2.9.7` - PostgreSQL adapter

### 2. Configure Environment Variables

Create a `.env` file with your Supabase credentials:

```bash
# Supabase Configuration
SUPABASE_URL=your-supabase-project-url
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# Optional: Direct database connection (for migrations)
SUPABASE_DB_HOST=your-db-host
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your-db-password
```

### 3. Apply Database Migration

Run the migration script to create the embeddings table:

```bash
python apply_migration.py
```

This will create:
- `embeddings` table with vector support
- Indexes for optimal performance
- Similarity search function
- Automatic timestamp updates

## Database Schema

The `embeddings` table structure:

```sql
CREATE TABLE embeddings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    chunk_id VARCHAR(255) NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    original_text TEXT NOT NULL,
    text_embedding vector(1536), -- OpenAI text-embedding-3-small
    all_embeddings JSONB, -- All generated embeddings
    extracted_data JSONB, -- Extracted structured data
    metadata JSONB, -- Processing metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Usage

### 1. Basic Document Processing with Storage

```python
from core.processor import document_processor

# Process documents and automatically store embeddings
documents = [
    {
        'chunk_id': 'chunk_1',
        'document_id': 'doc_1',
        'text': 'Your document text here...'
    }
]

schemas = ['contract_terms']
options = {'extract_entities': True}

result = document_processor.process_documents(documents, schemas, options)

# Check storage results
storage_results = result['summary']['storage_results']
print(f"Stored {storage_results['successful']} embeddings")
```

### 2. Vector Similarity Search

```python
# Search for similar documents
query_text = "artificial intelligence and machine learning"
similar_docs = document_processor.search_similar_documents(
    query_text, 
    limit=10, 
    similarity_threshold=0.7
)

for doc in similar_docs:
    print(f"Similarity: {doc['similarity']:.3f}")
    print(f"Text: {doc['original_text'][:100]}...")
    print("---")
```

### 3. Direct Vector Storage Operations

```python
from core.vector_storage import vector_storage

# Get storage statistics
stats = vector_storage.get_storage_stats()
print(f"Total embeddings: {stats['total_embeddings']}")

# Retrieve specific embedding
embedding = vector_storage.get_embedding_by_id('embedding-uuid')

# Delete embedding
success = vector_storage.delete_embedding('embedding-uuid')
```

## API Endpoints

New API endpoints have been added for vector operations:

### POST `/api/extract/`
Process documents and store embeddings automatically.

**Request:**
```json
{
    "documents": [
        {
            "chunk_id": "chunk_1",
            "document_id": "doc_1",
            "text": "Document text..."
        }
    ],
    "schemas": ["contract_terms"],
    "options": {"extract_entities": true}
}
```

### POST `/api/search/`
Search for similar documents using vector similarity.

**Request:**
```json
{
    "query_text": "search query",
    "limit": 10,
    "similarity_threshold": 0.7
}
```

### GET `/api/embeddings/{id}/`
Retrieve a specific embedding by ID.

### DELETE `/api/embeddings/{id}/delete/`
Delete a specific embedding by ID.

### GET `/api/vector-stats/`
Get vector storage statistics.

## Testing

Run the test script to verify the integration:

```bash
python test_vector_storage.py
```

This will test:
- System health
- Vector storage connection
- Document processing and storage
- Similarity search
- Embedding retrieval

## Performance Considerations

### Indexing
- The `text_embedding` column is indexed for fast similarity searches
- JSONB columns are indexed with GIN for efficient querying
- Consider adding additional indexes based on your query patterns

### Vector Dimensions
- Default: 1536 dimensions (OpenAI text-embedding-3-small)
- Adjust the migration if using different embedding models
- Higher dimensions = more storage but potentially better accuracy

### Batch Operations
- Use batch storage for multiple documents
- The system automatically handles batch operations efficiently

## Troubleshooting

### Common Issues

1. **pgvector extension not enabled**
   ```bash
   # Enable in Supabase SQL editor
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **Connection errors**
   - Verify your Supabase URL and keys
   - Check network connectivity
   - Ensure your IP is whitelisted if using RLS

3. **Migration failures**
   - Run the migration script with proper credentials
   - Check Supabase logs for detailed error messages
   - Verify pgvector extension is available

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks

Check system status:

```bash
curl http://localhost:8000/api/status/
```

## Security Considerations

1. **Row Level Security (RLS)**: Consider enabling RLS on the embeddings table
2. **API Keys**: Use service role keys only for server-side operations
3. **Data Privacy**: Ensure sensitive document content is properly handled
4. **Access Control**: Implement proper authentication for API endpoints

## Monitoring

Monitor your vector storage:

```python
# Get real-time stats
stats = vector_storage.get_storage_stats()
print(f"Storage status: {stats['status']}")
print(f"Total embeddings: {stats['total_embeddings']}")
```

## Scaling

The vector storage is designed to scale:

- **Horizontal scaling**: Add more Supabase instances
- **Vertical scaling**: Upgrade your Supabase plan
- **Caching**: Implement Redis for frequently accessed embeddings
- **Partitioning**: Consider table partitioning for large datasets

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Supabase documentation
3. Check the test scripts for examples
4. Enable debug logging for detailed error information

## Migration from Existing System

If you have an existing langextract system:

1. **Backup your data** before applying changes
2. **Test the integration** in a development environment
3. **Gradually migrate** documents to use the new storage
4. **Monitor performance** during the transition

The integration is designed to be non-disruptive to your existing functionality.
