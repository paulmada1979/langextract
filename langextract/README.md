# LangExtract

A Django-based document processing service that extracts structured data from text chunks according to predefined schemas and generates embeddings using OpenAI API.

## Features

- **Schema-Based Extraction**: Apply custom schemas to extract structured data from text chunks
- **OpenAI Integration**: Generate high-quality embeddings using OpenAI's text-embedding models
- **Modular Architecture**: Clean, maintainable codebase following Django best practices
- **RESTful API**: Comprehensive API endpoints for document processing and system management
- **Docker Support**: Containerized deployment with docker-compose
- **Rate Limiting**: Built-in API rate limiting and OpenAI API rate management

## Architecture

```
Text Chunks → Schema Extraction → Embedding Generation → Response
```

### Core Components

1. **Schema Loader**: Manages and loads schemas from YAML/JSON files
2. **Schema Extractor**: Applies schemas to text chunks and extracts structured data
3. **OpenAI Client**: Handles OpenAI API interactions and embedding generation
4. **Document Processor**: Orchestrates the entire processing pipeline
5. **API Layer**: RESTful endpoints for external integration

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and docker-compose
- OpenAI API key

### Environment Setup

1. Copy the environment file:

   ```bash
   cp env.example .env
   ```

2. Edit `.env` with your configuration:

   ```bash
   # Django Settings
   DEBUG=True
   DJANGO_SECRET_KEY=your-secret-key-here
   ALLOWED_HOSTS=localhost,127.0.0.1

   # OpenAI API
   OPENAI_API_KEY=your-openai-api-key-here
   OPENAI_MODEL=text-embedding-3-small

   # API Settings
   API_RATE_LIMIT=1000
   MAX_TOKENS_PER_REQUEST=8000
   ```

### Running with Docker

1. Build and start the service:

   ```bash
   docker-compose up --build
   ```

2. The service will be available at `http://localhost:8000`

### Running Locally

1. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run migrations:

   ```bash
   python manage.py migrate
   ```

4. Start the development server:
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Document Processing

**POST** `/api/process/`

Process document chunks and generate embeddings.

**Request Body:**

```json
{
  "documents": [
    {
      "text": "chunk text content here",
      "document_id": "abc123",
      "chunk_id": "chunk_001",
      "metadata": {
        "file_name": "contract.pdf",
        "page_number": 1,
        "section": "terms"
      }
    }
  ],
  "schemas": ["contract_terms", "invoice"],
  "options": {
    "extract_entities": true,
    "extract_categories": true,
    "confidence_threshold": 0.7
  }
}
```

**Response:**

```json
{
  "status": "success",
  "processed_documents": [
    {
      "chunk_id": "chunk_001",
      "document_id": "abc123",
      "content": "chunk text content here",
      "extracted_data": {
        "entities": [...],
        "categories": [...],
        "key_phrases": [...],
        "schema_matches": {...}
      },
      "embeddings": {
        "text": [...],
        "schemas": {...},
        "key_phrases": {...}
      },
      "metadata": {...}
    }
  ],
  "summary": {...}
}
```

### Schema Management

**GET** `/api/schemas/` - List all available schemas
**GET** `/api/schemas/{schema_name}/` - Get specific schema details

### System Management

**GET** `/api/status/` - System health and status
**GET** `/api/stats/` - Processing statistics
**GET** `/health/` - Basic health check

## Schema System

### Schema Structure

Schemas are defined in JSON format with the following structure:

```json
{
  "$id": "contract_terms",
  "version": "1.0.0",
  "description": "Key terms of a commercial contract.",
  "required": ["parties"],
  "fields": {
    "parties": { "type": "list", "items": { "type": "string" } },
    "effective_date": { "type": "string" },
    "term": { "type": "string" },
    "renewal": { "type": "string" },
    "payment_terms": { "type": "string" },
    "termination_clause": { "type": "string" },
    "governing_law": { "type": "string" },
    "signatures": { "type": "list", "items": { "type": "string" } }
  },
  "spans": ["payment_terms", "termination_clause"]
}
```

### Field Types

- **string**: Text fields with optional enum validation
- **list**: Arrays of values
- **number**: Numeric fields
- **object**: Nested structures

### Special Features

- **Spans**: Fields that extract text spans from the document
- **Enum References**: Link to vocabulary files for validation
- **Required Fields**: Validation of mandatory fields

## Configuration

### OpenAI Models

The service supports multiple OpenAI embedding models:

- `text-embedding-ada-002` (older, cheaper)
- `text-embedding-3-small` (newer, better quality, reasonable cost)
- `text-embedding-3-large` (highest quality, higher cost)

### Rate Limiting

- **API Rate Limits**: 100/minute for anonymous users, 1000/minute for authenticated users
- **OpenAI Rate Limits**: 3,000 requests per minute with built-in delays

## Development

### Project Structure

```
langextract/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── manage.py
├── langextract/          # Django project settings
├── api/                  # API endpoints and serializers
├── core/                 # Core business logic
│   ├── schema_loader.py
│   ├── schema_extractor.py
│   ├── openai_client.py
│   └── processor.py
├── schemas/              # Schema definitions
└── tests/                # Test suite
```

### Running Tests

```bash
python manage.py test
```

### Code Quality

The project follows Django best practices:

- Comprehensive error handling and logging
- Input validation with Django REST Framework serializers
- Modular architecture with clear separation of concerns
- Comprehensive test coverage
- Type hints for better code maintainability

## Deployment

### Production Considerations

1. Set `DEBUG=False` in production
2. Use a proper `DJANGO_SECRET_KEY`
3. Configure `ALLOWED_HOSTS` for your domain
4. Set up proper logging
5. Consider using a reverse proxy (nginx) for production

### Docker Production

```bash
# Build production image
docker build -t langextract:latest .

# Run with production settings
docker run -d \
  -p 8000:8000 \
  -e DEBUG=False \
  -e DJANGO_SECRET_KEY=your-production-secret \
  -e OPENAI_API_KEY=your-openai-key \
  langextract:latest
```

## Monitoring and Logging

The service includes comprehensive logging and monitoring:

- **Health Checks**: `/health/` and `/api/status/` endpoints
- **Processing Statistics**: `/api/stats/` endpoint
- **Structured Logging**: JSON-formatted logs with different levels
- **Error Tracking**: Detailed error logging with context

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:

1. Check the API documentation
2. Review the logs for error details
3. Test the system status endpoint
4. Open an issue on GitHub

## Changelog

### v1.0.0

- Initial release
- Schema-based document processing
- OpenAI embedding integration
- RESTful API endpoints
- Docker support
