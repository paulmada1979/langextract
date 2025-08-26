"""
URL patterns for the API app.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Document processing
    path('process/', views.process_documents, name='process_documents'),
    
    # Schema management
    path('schemas/', views.list_schemas, name='list_schemas'),
    path('schemas/<str:schema_name>/', views.get_schema, name='get_schema'),
    
    # System management
    path('status/', views.system_status, name='system_status'),
    path('stats/', views.processing_stats, name='processing_stats'),
]
