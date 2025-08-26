# LangExtract - Structured Implementation Plan

## Project Overview

LangExtract is a Django-based document processing service that extracts structured data from text chunks according to predefined schemas and generates embeddings. The service receives text chunks via API requests and returns schema-based extractions with embeddings. The pipeline is: Text Chunks → Schema Extraction → Embedding Generation → Response.

## Architecture Components

### 1. Core Service (Django)

- **Framework**: Django 4.x with Django REST Framework
- **Containerization**: Docker with docker-compose
- **API**: RESTful API with JSON input/output
- **Stateless**: No persistent storage required

### 2. Schema System

Based on analysis of `./schema/` folder, the system supports:

#### Core Schemas (`schemas-core/`)

- **contract_terms.json**: Commercial contract key terms
- **invoice.json**: Invoice data extraction
- **refund_case.json**: Refund case processing
- **support_case.json**: Customer support cases
- **product_spec.json**: Product specifications
- **price_list.json**: Pricing information
- **policy.json**: Policy documents
- **faq.json**: Frequently asked questions

#### Domain-Specific Schemas (`schemas-domains/`)

- **retail/**: Retail-specific extensions for refund cases and product specs

#### Vocabulary Schemas (`schemas-vocab/`)

- **currencies.yaml**: ISO currency codes (USD, EUR, GBP, NGN, CNY)
- **sop_steps.json**: Standard operating procedure steps

#### Schema Registry (`registry.yaml`)

- Central configuration for schema application
- Support for company-specific overrides via `${COMPANY_ID}` variables
- Layered schema application (core + domain + company-specific)

### 3. OpenAI Integration

- **Embedding Model**: OpenAI text-embedding-ada-002 or text-embedding-3-small/large
- **API Integration**: OpenAI API client with proper rate limiting and error handling
- **Vector Generation**: Generate embeddings for extracted schema data and text chunks
- **Model Management**: OpenAI API key management and configuration
- **Performance**: Optimized for OpenAI API response times and rate limits

## API Specification

### Input Format

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
  "schemas": ["contract_terms", "invoice", "refund_case"],
  "options": {
    "extract_entities": true,
    "extract_categories": true,
    "confidence_threshold": 0.7
  }
}
```

### Output Format

```json
{
  "status": "success",
  "processed_documents": [
    {
      "chunk_id": "chunk_001",
      "document_id": "abc123",
      "original_text": "original chunk text",
      "extracted_data": {
        "entities": [
          { "text": "John Doe", "label": "PERSON", "confidence": 0.95 },
          { "text": "$50,000", "label": "MONEY", "confidence": 0.89 }
        ],
        "categories": [
          { "name": "legal_contract", "confidence": 0.92 },
          { "name": "indemnification", "confidence": 0.78 }
        ],
        "key_phrases": ["indemnification clause", "party obligations"],
        "schema_matches": {
          "contract_terms": {
            "parties": ["Company A", "Company B"],
            "effective_date": "2024-01-01",
            "governing_law": "Delaware"
          }
        }
      },
      "metadata": {
        "processing_time": 0.234,
        "schemas_applied": ["contract_terms"]
      }
    }
  ],
  "summary": {
    "total_chunks": 1,
    "processed_chunks": 1,
    "failed_chunks": 0,
    "total_processing_time": 0.234
  }
}
```

## Implementation Phases

### Phase 1: Project Setup & Core Infrastructure

1. **Django Project Initialization**

   - Create Django project with REST framework
   - Set up Docker and docker-compose
   - Configure PostgreSQL connection
   - Set up basic project structure

2. **Schema Management System**
   - Implement schema loader from YAML/JSON files
   - Create schema registry service
   - Build schema validation system
   - Support for layered schema application

### Phase 2: Core Extraction Engine

1. **Schema-Based Extraction Pipeline**

   - Process text chunks from API requests
   - Schema field extraction and validation
   - OpenAI-assisted field extraction for complex cases
   - Entity extraction (NER) for additional context
   - Category classification based on schema matches
   - Key phrase extraction for search optimization

2. **Schema Matching Engine**
   - Field extraction based on schema definitions
   - Span identification for text fields
   - Enum validation (e.g., currencies)
   - Required field validation

### Phase 3: OpenAI Integration

1. **OpenAI API Integration**

   - OpenAI API client setup and configuration
   - API key management and security
   - Rate limiting and error handling
   - Embedding generation for text chunks and schema fields

2. **Confidence Scoring**
   - ML model integration for confidence assessment
   - Threshold-based filtering
   - Quality metrics

### Phase 4: API & Integration

1. **REST API Development**

   - Document chunk processing endpoint
   - Schema-based extraction endpoint
   - Embedding generation endpoint
   - Schema management endpoints
   - Health check and monitoring

2. **Response Optimization**
   - Structured JSON responses with embeddings
   - Performance optimization for embedding generation
   - Error handling and validation
   - API rate limiting and monitoring

## Technical Requirements

### OpenAI API Considerations

- **API Models**:
  - `text-embedding-ada-002` (older, cheaper)
  - `text-embedding-3-small` (newer, better quality, reasonable cost)
  - `text-embedding-3-large` (highest quality, higher cost)
- **Rate Limits**: 3,000 requests per minute for most models
- **Token Limits**: 8,191 tokens per request for ada-002, 8,192 for v3 models
- **Cost Optimization**: Batch processing and efficient token usage
- **API Key Security**: Environment variables and secure key management

### Dependencies

- **Django**: 4.x
- **Django REST Framework**: 3.x
- **Python**: 3.11+
- **Docker**: 24.x
- **AI/ML Libraries**: spaCy, transformers
- **OpenAI Integration**: openai Python library, API key management

### File Structure

```
langextract/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── manage.py
├── langextract/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── api/
│   ├── __init__.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── core/
│   ├── __init__.py
│   ├── schema_loader.py
│   ├── extractor.py
│   └── processor.py
├── schemas/          # Copy from ./schema/
└── tests/
```

## Schema Processing Logic

### 1. Schema Loading

- Parse `registry.yaml` to understand available schemas
- Load core schemas from `schemas-core/`
- Apply domain-specific extensions from `schemas-domains/`
- Support company-specific overrides

### 2. Field Extraction

- **String Fields**: Direct text extraction
- **List Fields**: Multi-value extraction
- **Object Fields**: Nested structure extraction
- **Enum Fields**: Validation against vocabulary (e.g., currencies)
- **Span Fields**: Text span identification with confidence
- **OpenAI Assistance**: Use OpenAI for complex field extraction and validation

### 3. Validation & Quality

- Required field validation
- Data type validation
- Enum value validation
- Confidence threshold filtering

## Next Steps

1. **Immediate Actions**

   - Set up Django project structure
   - Create Docker configuration
   - Implement basic schema loader
   - Design API endpoints for chunk processing

2. **Week 1-2**

   - Core extraction engine development
   - Basic API endpoints for chunk processing
   - Schema extraction implementation

3. **Week 3-4**

   - Embedding generation integration
   - API response optimization
   - Performance testing and tuning

4. **Week 5-6**
   - Testing and optimization
   - Documentation and deployment

## Success Metrics

- **Processing Accuracy**: >90% field extraction accuracy
- **Performance**: <2 seconds per document chunk (accounting for OpenAI API latency)
- **Scalability**: Support for 1000+ concurrent requests with OpenAI rate limiting
- **Reliability**: 99.9% uptime with proper error handling
- **Embedding Quality**: High-quality OpenAI embeddings for schema fields and text chunks
- **OpenAI API Efficiency**: Optimized token usage and API call management
