"""
URL patterns for the API app.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Document processing and embedding storage
    path('extract/', views.extract_schemas, name='extract_schemas'),
    path('process/', views.extract_schemas, name='process_documents'),  # Backward compatibility
    
    # Schema management
    path('schemas/', views.list_schemas, name='list_schemas'),
    
    # System management
    path('health/', views.health_check, name='health_check'),
    path('status/', views.system_status, name='system_status'),
    
    # Vector search and storage
    path('search/', views.search_similar_documents, name='search_similar_documents'),
    path('embeddings/<str:embedding_id>/', views.get_embedding_by_id, name='get_embedding_by_id'),
    path('embeddings/<str:embedding_id>/delete/', views.delete_embedding, name='delete_embedding'),
    path('vector-stats/', views.vector_storage_stats, name='vector_storage_stats'),
]
