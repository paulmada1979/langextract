"""
Document processor app configuration.
"""

from django.apps import AppConfig


class DocumentProcessorConfig(AppConfig):
    """Document processor app configuration."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'document_processor'
    verbose_name = 'Document Processor'
