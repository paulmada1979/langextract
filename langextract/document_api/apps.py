"""
Document API app configuration.
"""

from django.apps import AppConfig


class DocumentApiConfig(AppConfig):
    """Document API app configuration."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'document_api'
    verbose_name = 'Document API'
