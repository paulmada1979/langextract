"""
API serializers for request and response validation.
"""

from rest_framework import serializers
from typing import Dict, List, Any


class DocumentMetadataSerializer(serializers.Serializer):
    """Serializer for document metadata."""
    file_name = serializers.CharField(required=False, allow_blank=True)
    page_number = serializers.IntegerField(required=False, min_value=1)
    section = serializers.CharField(required=False, allow_blank=True)


class DocumentChunkSerializer(serializers.Serializer):
    """Serializer for document chunks."""
    text = serializers.CharField(required=True, max_length=32000)  # OpenAI token limit
    document_id = serializers.CharField(required=True, max_length=100)
    chunk_id = serializers.CharField(required=True, max_length=100)
    metadata = DocumentMetadataSerializer(required=False)


class ProcessingOptionsSerializer(serializers.Serializer):
    """Serializer for processing options."""
    extract_entities = serializers.BooleanField(default=True)
    extract_categories = serializers.BooleanField(default=True)
    confidence_threshold = serializers.FloatField(default=0.7, min_value=0.0, max_value=1.0)


class DocumentProcessingRequestSerializer(serializers.Serializer):
    """Serializer for document processing requests."""
    documents = DocumentChunkSerializer(many=True, required=True)
    schemas = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=True,
        min_length=1
    )
    options = ProcessingOptionsSerializer(required=False)


class EntitySerializer(serializers.Serializer):
    """Serializer for extracted entities."""
    text = serializers.CharField()
    label = serializers.CharField()
    confidence = serializers.FloatField(min_value=0.0, max_value=1.0)


class CategorySerializer(serializers.Serializer):
    """Serializer for extracted categories."""
    name = serializers.CharField()
    confidence = serializers.FloatField(min_value=0.0, max_value=1.0)


class ExtractedDataSerializer(serializers.Serializer):
    """Serializer for extracted data."""
    entities = EntitySerializer(many=True)
    categories = CategorySerializer(many=True)
    key_phrases = serializers.ListField(child=serializers.CharField())
    schema_matches = serializers.DictField()


class EmbeddingSerializer(serializers.Serializer):
    """Serializer for embeddings."""
    text = serializers.ListField(child=serializers.FloatField(), required=False)
    schemas = serializers.DictField(required=False)
    key_phrases = serializers.DictField(required=False)


class ProcessedDocumentMetadataSerializer(serializers.Serializer):
    """Serializer for processed document metadata."""
    processing_time = serializers.FloatField()
    schemas_applied = serializers.ListField(child=serializers.CharField())
    embedding_model = serializers.CharField()


class ProcessedDocumentSerializer(serializers.Serializer):
    """Serializer for processed documents."""
    chunk_id = serializers.CharField()
    document_id = serializers.CharField()
    original_text = serializers.CharField()
    extracted_data = ExtractedDataSerializer()
    embeddings = EmbeddingSerializer()
    metadata = ProcessedDocumentMetadataSerializer()


class ProcessingSummarySerializer(serializers.Serializer):
    """Serializer for processing summary."""
    total_chunks = serializers.IntegerField()
    processed_chunks = serializers.IntegerField()
    failed_chunks = serializers.IntegerField()
    total_processing_time = serializers.FloatField()


class DocumentProcessingResponseSerializer(serializers.Serializer):
    """Serializer for document processing responses."""
    status = serializers.CharField()
    processed_documents = ProcessedDocumentSerializer(many=True)
    summary = ProcessingSummarySerializer()


class SchemaInfoSerializer(serializers.Serializer):
    """Serializer for schema information."""
    name = serializers.CharField()
    description = serializers.CharField(required=False)
    version = serializers.CharField(required=False)
    fields = serializers.DictField(required=False)


class SystemStatusSerializer(serializers.Serializer):
    """Serializer for system status."""
    status = serializers.CharField()
    openai_connection = serializers.BooleanField()
    schema_loading = serializers.BooleanField()
    text_processing = serializers.BooleanField()
    available_schemas = serializers.ListField(child=serializers.CharField())
    openai_model = serializers.DictField()
