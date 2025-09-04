"""
Serializers for document API endpoints.
"""

from rest_framework import serializers
from typing import Dict, List, Any, Optional


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload requests."""
    
    file = serializers.FileField(required=True)
    userId = serializers.UUIDField(required=True, help_text="UUID of the user uploading the document")
    schemas = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=['invoice', 'support_case', 'refund_case'],
        help_text="List of schemas to apply for metadata extraction"
    )
    enable_docling = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Enable docling for document processing (default: True for all supported formats)"
    )
    processing_options = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Additional processing options"
    )
    
    def validate_file(self, value):
        """Validate uploaded file."""
        # Check file size (50MB limit)
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 50MB")
        
        # Check file extension
        allowed_extensions = ['.pdf', '.docx', '.doc', '.md', '.txt']
        file_extension = value.name.lower().split('.')[-1] if '.' in value.name else ''
        
        if f'.{file_extension}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"Unsupported file format. Allowed formats: {', '.join(allowed_extensions)}"
            )
        
        return value
    
    def validate_schemas(self, value):
        """Validate schema list."""
        allowed_schemas = [
            'support_case', 'refund_case', 'invoice', 'contract_terms',
            'sop_steps', 'price_list', 'product_spec', 'faq', 'policy'
        ]
        
        invalid_schemas = [s for s in value if s not in allowed_schemas]
        if invalid_schemas:
            raise serializers.ValidationError(
                f"Invalid schemas: {invalid_schemas}. Allowed schemas: {allowed_schemas}"
            )
        
        return value


class DocumentSerializer(serializers.Serializer):
    """Serializer for document information."""
    
    id = serializers.UUIDField(read_only=True)
    filename = serializers.CharField(read_only=True)
    original_filename = serializers.CharField(read_only=True)
    file_type = serializers.CharField(read_only=True)
    file_size = serializers.IntegerField(read_only=True)
    upload_status = serializers.CharField(read_only=True)
    processing_status = serializers.CharField(read_only=True)
    processing_error = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    processed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    metadata = serializers.JSONField(read_only=True)


class DocumentStatusSerializer(serializers.Serializer):
    """Serializer for document processing status."""
    
    document_id = serializers.UUIDField()
    status = serializers.CharField()
    message = serializers.CharField(required=False)
    progress = serializers.FloatField(required=False, min_value=0.0, max_value=1.0)
    chunks_processed = serializers.IntegerField(required=False)
    total_chunks = serializers.IntegerField(required=False)


class ChunkSerializer(serializers.Serializer):
    """Serializer for document chunks."""
    
    id = serializers.UUIDField(read_only=True)
    chunk_id = serializers.CharField(read_only=True)
    chunk_index = serializers.IntegerField(read_only=True)
    content = serializers.CharField(read_only=True)
    content_type = serializers.CharField(read_only=True)
    extracted_metadata = serializers.JSONField(read_only=True)
    chunk_metadata = serializers.JSONField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class DocumentDetailSerializer(DocumentSerializer):
    """Extended serializer for document details including chunks."""
    
    chunks = ChunkSerializer(many=True, read_only=True)
    stats = serializers.JSONField(read_only=True)


class ChatSessionSerializer(serializers.Serializer):
    """Serializer for chat sessions."""
    
    id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(required=True, help_text="UUID of the user who owns this chat session")
    session_name = serializers.CharField(max_length=255)
    document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list
    )
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    last_activity = serializers.DateTimeField(read_only=True)


class ChatMessageSerializer(serializers.Serializer):
    """Serializer for chat messages."""
    
    id = serializers.UUIDField(read_only=True)
    session_id = serializers.UUIDField()
    message_type = serializers.ChoiceField(choices=['user', 'assistant', 'system'])
    content = serializers.CharField()
    metadata = serializers.JSONField(required=False, default=dict)
    referenced_chunks = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list
    )
    created_at = serializers.DateTimeField(read_only=True)


class ChatRequestSerializer(serializers.Serializer):
    """Serializer for chat requests."""
    
    message = serializers.CharField(max_length=2000)
    userId = serializers.UUIDField(required=True, help_text="UUID of the user sending the message")
    document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
        help_text="Optional: specific document IDs to search. If not provided, searches all user's documents."
    )
    include_sources = serializers.BooleanField(default=True)
    max_tokens = serializers.IntegerField(default=1000, min_value=100, max_value=4000)
    temperature = serializers.FloatField(default=0.7, min_value=0.0, max_value=2.0)


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chat responses."""
    
    message = serializers.CharField()
    session_id = serializers.UUIDField()
    message_id = serializers.UUIDField()
    referenced_chunks = serializers.ListField(
        child=serializers.JSONField(),
        required=False,
        default=list
    )
    sources = serializers.ListField(
        child=serializers.JSONField(),
        required=False,
        default=list
    )
    metadata = serializers.JSONField(required=False, default=dict)


class SearchRequestSerializer(serializers.Serializer):
    """Serializer for document search requests."""
    
    query = serializers.CharField(max_length=500)
    document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list
    )
    limit = serializers.IntegerField(default=10, min_value=1, max_value=50)
    similarity_threshold = serializers.FloatField(default=0.7, min_value=0.0, max_value=1.0)
    content_type_filter = serializers.CharField(required=False, allow_null=True)


class SearchResultSerializer(serializers.Serializer):
    """Serializer for search results."""
    
    id = serializers.UUIDField(read_only=True)
    document_id = serializers.UUIDField(read_only=True)
    chunk_id = serializers.CharField(read_only=True)
    chunk_index = serializers.IntegerField(read_only=True)
    content = serializers.CharField(read_only=True)
    content_type = serializers.CharField(read_only=True)
    similarity = serializers.FloatField(read_only=True)
    extracted_metadata = serializers.JSONField(read_only=True)
    chunk_metadata = serializers.JSONField(read_only=True)


class DocumentStatsSerializer(serializers.Serializer):
    """Serializer for document statistics."""
    
    total_documents = serializers.IntegerField(read_only=True)
    total_chunks = serializers.IntegerField(read_only=True)
    total_size = serializers.IntegerField(read_only=True)
    processing_status_counts = serializers.JSONField(read_only=True)
    file_type_counts = serializers.JSONField(read_only=True)
    recent_uploads = serializers.ListField(
        child=DocumentSerializer(),
        read_only=True
    )


class ErrorSerializer(serializers.Serializer):
    """Serializer for error responses."""
    
    error = serializers.CharField()
    message = serializers.CharField(required=False)
    details = serializers.JSONField(required=False)
    timestamp = serializers.DateTimeField(read_only=True)
