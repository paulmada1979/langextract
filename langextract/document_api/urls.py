"""
URL patterns for document API endpoints.
"""

from django.urls import path
from . import views

app_name = 'document_api'

urlpatterns = [
    # Document endpoints
    path('documents/upload/', views.DocumentAPIView.upload_document, name='upload_document'),
    path('documents/', views.DocumentAPIView.list_documents, name='list_documents'),
    path('documents/<uuid:document_id>/', views.DocumentAPIView.get_document, name='get_document'),
    path('documents/<uuid:document_id>/status/', views.DocumentAPIView.get_document_status, name='get_document_status'),
    path('documents/<uuid:document_id>/delete/', views.DocumentAPIView.delete_document, name='delete_document'),
    path('documents/search/', views.DocumentAPIView.search_documents, name='search_documents'),
    path('documents/stats/', views.DocumentAPIView.get_stats, name='get_stats'),
    
    # Chat endpoints
    path('chat/sessions/', views.ChatAPIView.create_chat_session, name='create_chat_session'),
    path('chat/sessions/list/', views.ChatAPIView.list_chat_sessions, name='list_chat_sessions'),
    path('chat/sessions/<uuid:session_id>/', views.ChatAPIView.get_chat_session, name='get_chat_session'),
    path('chat/sessions/<uuid:session_id>/delete/', views.ChatAPIView.delete_chat_session, name='delete_chat_session'),
    path('chat/message/', views.ChatAPIView.send_message, name='send_message'),
    path('chat/', views.DocumentAPIView.chat_interface, name='chat_interface'),
]
