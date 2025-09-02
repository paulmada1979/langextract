"""
API views for document processing and AI chat functionality.
"""

import logging
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.shortcuts import render

from .serializers import (
    DocumentUploadSerializer, DocumentSerializer, DocumentStatusSerializer,
    ChunkSerializer, DocumentDetailSerializer, ChatSessionSerializer,
    ChatMessageSerializer, ChatRequestSerializer, ChatResponseSerializer,
    SearchRequestSerializer, SearchResultSerializer, DocumentStatsSerializer,
    ErrorSerializer
)
from document_processor import DocumentProcessor
from core.supabase_client import supabase_client
from core.openai_client import openai_client

logger = logging.getLogger(__name__)


class DocumentAPIView:
    """API view for document operations."""
    
    def __init__(self):
        self.processor = DocumentProcessor()
    
    @staticmethod
    @csrf_exempt
    @api_view(['POST'])
    @permission_classes([AllowAny])
    def upload_document(request):
        """Upload and process a document."""
        try:
            serializer = DocumentUploadSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'error': 'Validation failed',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            file = serializer.validated_data['file']
            user_id = serializer.validated_data['userId']
            schemas = serializer.validated_data.get('schemas', ['invoice', 'support_case', 'refund_case'])
            
            # Read file data
            file_data = file.read()
            filename = file.name
            
            # Process document asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    DocumentAPIView().processor.process_document(file_data, filename, str(user_id), schemas)
                )
                
                return Response({
                    'success': True,
                    'message': 'Document uploaded and processed successfully',
                    'data': result
                }, status=status.HTTP_201_CREATED)
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Document upload failed: {e}")
            return Response({
                'error': 'Document processing failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    @api_view(['GET'])
    @permission_classes([AllowAny])
    def list_documents(request):
        """List all uploaded documents."""
        try:
            limit = int(request.GET.get('limit', 50))
            offset = int(request.GET.get('offset', 0))
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                documents = loop.run_until_complete(
                    DocumentAPIView().processor.list_documents(limit, offset)
                )
                
                serializer = DocumentSerializer(documents, many=True)
                
                return Response({
                    'success': True,
                    'data': serializer.data,
                    'count': len(documents)
                })
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return Response({
                'error': 'Failed to list documents',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    @api_view(['GET'])
    @permission_classes([AllowAny])
    def get_document(request, document_id):
        """Get document details and chunks."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Get document status
                document = loop.run_until_complete(
                    DocumentAPIView().processor.get_document_status(document_id)
                )
                
                if not document:
                    return Response({
                        'error': 'Document not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Get document chunks if available
                chunks = []
                if supabase_client.is_available():
                    client = supabase_client.get_client()
                    chunks_response = client.table('langextract_processed_embeddings').select('*').eq('document_id', document_id).order('chunk_index').execute()
                    chunks = chunks_response.data or []
                
                # Get document stats
                stats = {}
                if supabase_client.is_available():
                    client = supabase_client.get_client()
                    stats_response = client.rpc('get_document_stats', {'document_id': document_id}).execute()
                    if stats_response.data:
                        stats = stats_response.data[0]
                
                document['chunks'] = chunks
                document['stats'] = stats
                
                serializer = DocumentDetailSerializer(document)
                
                return Response({
                    'success': True,
                    'data': serializer.data
                })
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return Response({
                'error': 'Failed to get document',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    @api_view(['GET'])
    @permission_classes([AllowAny])
    def get_document_status(request, document_id):
        """Get document processing status."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                document = loop.run_until_complete(
                    DocumentAPIView().processor.get_document_status(document_id)
                )
                
                if not document:
                    return Response({
                        'error': 'Document not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                serializer = DocumentStatusSerializer({
                    'document_id': document['id'],
                    'status': document['processing_status'],
                    'message': document.get('processing_error', ''),
                    'chunks_processed': document.get('chunks_processed', 0),
                    'total_chunks': document.get('total_chunks', 0)
                })
                
                return Response({
                    'success': True,
                    'data': serializer.data
                })
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Failed to get document status {document_id}: {e}")
            return Response({
                'error': 'Failed to get document status',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    @api_view(['DELETE'])
    @permission_classes([AllowAny])
    def delete_document(request, document_id):
        """Delete a document and all its chunks."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                success = loop.run_until_complete(
                    DocumentAPIView().processor.delete_document(document_id)
                )
                
                if success:
                    return Response({
                        'success': True,
                        'message': 'Document deleted successfully'
                    })
                else:
                    return Response({
                        'error': 'Document not found or could not be deleted'
                    }, status=status.HTTP_404_NOT_FOUND)
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return Response({
                'error': 'Failed to delete document',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    @api_view(['GET'])
    @permission_classes([AllowAny])
    def search_documents(request):
        """Search documents using vector similarity."""
        try:
            serializer = SearchRequestSerializer(data=request.GET)
            if not serializer.is_valid():
                return Response({
                    'error': 'Validation failed',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            query = serializer.validated_data['query']
            document_ids = serializer.validated_data.get('document_ids', [])
            limit = serializer.validated_data.get('limit', 10)
            similarity_threshold = serializer.validated_data.get('similarity_threshold', 0.7)
            content_type_filter = serializer.validated_data.get('content_type_filter')
            
            # Generate query embedding
            if not openai_client.is_available():
                return Response({
                    'error': 'OpenAI client not available'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            try:
                query_embedding = openai_client.generate_embedding(query)
                
                # Search in database
                if not supabase_client.is_available():
                    return Response({
                        'error': 'Database not available'
                    }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
                client = supabase_client.get_client()
                
                # Prepare search parameters
                search_params = {
                    'query_embedding': query_embedding,
                    'match_threshold': similarity_threshold,
                    'match_count': limit
                }
                
                if document_ids:
                    search_params['document_ids'] = [str(doc_id) for doc_id in document_ids]
                
                if content_type_filter:
                    search_params['content_type_filter'] = content_type_filter
                
                # Execute search
                response = client.rpc('search_langextract_processed_embeddings', search_params).execute()
                
                results = response.data or []
                
                serializer = SearchResultSerializer(results, many=True)
                
                return Response({
                    'success': True,
                    'data': serializer.data,
                    'count': len(results),
                    'query': query
                })
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return Response({
                'error': 'Document search failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    @api_view(['GET'])
    @permission_classes([AllowAny])
    def get_stats(request):
        """Get system statistics."""
        try:
            if not supabase_client.is_available():
                return Response({
                    'error': 'Database not available'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            client = supabase_client.get_client()
            
            # Get document counts
            docs_response = client.table('langextract_documents').select('id, file_type, processing_status, file_size', count='exact').execute()
            documents = docs_response.data or []
            
            # Get chunk counts
            chunks_response = client.table('langextract_processed_embeddings').select('id', count='exact').execute()
            total_chunks = chunks_response.count if hasattr(chunks_response, 'count') else 0
            
            # Calculate statistics
            total_documents = len(documents)
            total_size = sum(doc.get('file_size', 0) for doc in documents)
            
            # Processing status counts
            status_counts = {}
            for doc in documents:
                status = doc.get('processing_status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # File type counts
            type_counts = {}
            for doc in documents:
                file_type = doc.get('file_type', 'unknown')
                type_counts[file_type] = type_counts.get(file_type, 0) + 1
            
            # Recent uploads
            recent_response = client.table('langextract_documents').select('*').order('created_at', desc=True).limit(5).execute()
            recent_uploads = recent_response.data or []
            
            stats = {
                'total_documents': total_documents,
                'total_chunks': total_chunks,
                'total_size': total_size,
                'processing_status_counts': status_counts,
                'file_type_counts': type_counts,
                'recent_uploads': recent_uploads
            }
            
            serializer = DocumentStatsSerializer(stats)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return Response({
                'error': 'Failed to get statistics',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    @api_view(['GET'])
    @permission_classes([AllowAny])
    def chat_interface(request):
        """Serve the chat interface."""
        return render(request, 'document_chat.html')


class ChatAPIView:
    """API view for AI chat functionality."""
    
    @staticmethod
    @csrf_exempt
    @api_view(['POST'])
    @permission_classes([AllowAny])
    def create_chat_session(request):
        """Create a new chat session."""
        try:
            serializer = ChatSessionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'error': 'Validation failed',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not supabase_client.is_available():
                return Response({
                    'error': 'Database not available'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            client = supabase_client.get_client()
            
            session_data = {
                'id': str(uuid.uuid4()),
                'session_name': serializer.validated_data.get('session_name', 'New Chat'),
                'document_ids': serializer.validated_data.get('document_ids', []),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'last_activity': datetime.utcnow().isoformat()
            }
            
            response = client.table('langextract_chat_sessions').insert(session_data).execute()
            
            if response.data:
                session_serializer = ChatSessionSerializer(response.data[0])
                return Response({
                    'success': True,
                    'message': 'Chat session created successfully',
                    'data': session_serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': 'Failed to create chat session'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Failed to create chat session: {e}")
            return Response({
                'error': 'Failed to create chat session',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    @api_view(['GET'])
    @permission_classes([AllowAny])
    def list_chat_sessions(request):
        """List all chat sessions."""
        try:
            if not supabase_client.is_available():
                return Response({
                    'error': 'Database not available'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            client = supabase_client.get_client()
            response = client.table('langextract_chat_sessions').select('*').order('last_activity', desc=True).execute()
            
            sessions = response.data or []
            serializer = ChatSessionSerializer(sessions, many=True)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'count': len(sessions)
            })
            
        except Exception as e:
            logger.error(f"Failed to list chat sessions: {e}")
            return Response({
                'error': 'Failed to list chat sessions',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    @api_view(['GET'])
    @permission_classes([AllowAny])
    def get_chat_session(request, session_id):
        """Get chat session details and messages."""
        try:
            if not supabase_client.is_available():
                return Response({
                    'error': 'Database not available'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            client = supabase_client.get_client()
            
            # Get session
            session_response = client.table('langextract_chat_sessions').select('*').eq('id', session_id).execute()
            if not session_response.data:
                return Response({
                    'error': 'Chat session not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            session = session_response.data[0]
            
            # Get messages
            messages_response = client.table('langextract_chat_messages').select('*').eq('session_id', session_id).order('created_at').execute()
            messages = messages_response.data or []
            
            session['messages'] = messages
            
            session_serializer = ChatSessionSerializer(session)
            messages_serializer = ChatMessageSerializer(messages, many=True)
            
            return Response({
                'success': True,
                'data': {
                    'session': session_serializer.data,
                    'messages': messages_serializer.data
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to get chat session {session_id}: {e}")
            return Response({
                'error': 'Failed to get chat session',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    @csrf_exempt
    @api_view(['POST'])
    @permission_classes([AllowAny])
    def send_message(request):
        """Send a message to the AI chat."""
        try:
            serializer = ChatRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'error': 'Validation failed',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            message = serializer.validated_data['message']
            user_id = serializer.validated_data['userId']
            document_ids = serializer.validated_data.get('document_ids', [])
            include_sources = serializer.validated_data.get('include_sources', True)
            max_tokens = serializer.validated_data.get('max_tokens', 500)  # Reduced from 1000 to 500 for cost optimization
            temperature = serializer.validated_data.get('temperature', 0.3)  # Reduced from 0.7 to 0.3 for more focused responses
            
            # Process chat message
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    ChatAPIView._process_chat_message(
                        message, user_id, document_ids, include_sources, max_tokens, temperature
                    )
                )
                
                return Response({
                    'success': True,
                    'data': result
                })
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Chat message processing failed: {e}")
            return Response({
                'error': 'Chat message processing failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def _convert_uuids_to_strings(obj):
        """Recursively convert UUID objects to strings in nested data structures."""
        if hasattr(obj, '__class__') and 'UUID' in str(obj.__class__):
            return str(obj)
        elif isinstance(obj, dict):
            return {key: ChatAPIView._convert_uuids_to_strings(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [ChatAPIView._convert_uuids_to_strings(item) for item in obj]
        else:
            return obj
    
    @staticmethod
    async def _process_chat_message(message: str, user_id: str, document_ids: List[str], 
                                  include_sources: bool, max_tokens: int = 500, temperature: float = 0.3) -> Dict[str, Any]:
        """Process a chat message and generate response."""
        try:
            if not supabase_client.is_available():
                raise RuntimeError("Database not available")
            
            client = supabase_client.get_client()
            
            # No need to store user messages since we're not using sessions
            
            # Search for relevant chunks across all documents
            relevant_chunks = []
            if openai_client.is_available():
                # Generate query embedding
                query_embedding = openai_client.generate_embedding(message)
                
                if query_embedding:
                    # Search for relevant chunks
                    search_params = {
                        'query_embedding': query_embedding,
                        'filter_user_id': str(user_id),  # Convert UUID to string
                        'document_ids': [str(doc_id) for doc_id in document_ids] if document_ids else None,  # Convert UUIDs to strings
                        'match_threshold': 0.3,  # Lower threshold to be more permissive
                        'match_count': 10
                    }
                    
                    search_response = client.rpc('search_langextract_processed_embeddings', search_params).execute()
                    relevant_chunks = search_response.data or []
                    
                    # Convert all UUID objects to strings in the chunks data
                    for chunk in relevant_chunks:
                        for key, value in chunk.items():
                            if hasattr(value, '__class__') and 'UUID' in str(value.__class__):
                                chunk[key] = str(value)
                            elif key in ['id', 'document_id'] and value:
                                chunk[key] = str(value)
            
            # Generate AI response
            ai_response = ""
            referenced_chunk_ids = []
            
            if openai_client.is_available() and relevant_chunks:
                # Prepare context from relevant chunks
                context = ""
                for chunk in relevant_chunks[:5]:  # Use top 5 chunks
                    context += f"\n\nDocument Section {chunk['chunk_index'] + 1}:\n{chunk['content']}"
                    referenced_chunk_ids.append(str(chunk['id']))
                
                # Generate response using OpenAI completion
                prompt = f"""Based on the following document context, please answer the user's question. Be helpful, accurate, and concise. If the context doesn't contain enough information to fully answer the question, please say so.

Document Context:
{context}

User Question: {message}

Please provide a clear and helpful response based on the document content:"""
                
                # Generate AI response using OpenAI
                ai_response = openai_client.generate_completion(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # Fallback if completion fails
                if not ai_response:
                    ai_response = f"I found {len(relevant_chunks)} relevant sections in the documents, but I'm having trouble generating a response at the moment. Here's what I found: {context[:200]}..."
                    
            elif relevant_chunks:
                # If we have chunks but no OpenAI, provide a basic response
                context = "\n\n".join([chunk['content'][:200] + "..." for chunk in relevant_chunks[:3]])
                ai_response = f"Based on the document content, I found relevant information: {context}"
                referenced_chunk_ids = [str(chunk['id']) for chunk in relevant_chunks[:3]]
            else:
                ai_response = "I couldn't find any relevant information in the documents to answer your question. Please try rephrasing your question or check if the documents contain the information you're looking for."
            
            # Prepare response with proper UUID serialization
            response_data = {
                'message': ai_response,
                'user_id': str(user_id),
                'message_id': str(uuid.uuid4()),
                'referenced_chunks': referenced_chunk_ids,
                'sources': [
                    {
                        'id': chunk['id'],
                        'document_id': chunk['document_id'],
                        'chunk_id': chunk['chunk_id'],
                        'chunk_index': chunk['chunk_index'],
                        'content': chunk['content'][:200] + '...' if len(chunk['content']) > 200 else chunk['content'],
                        'content_type': chunk['content_type'],
                        'similarity': float(chunk['similarity']) if 'similarity' in chunk else None
                    }
                    for chunk in relevant_chunks[:3]
                ] if include_sources else [],
                'metadata': {
                    'chunks_searched': len(relevant_chunks),
                    'chunks_used': len(referenced_chunk_ids)
                }
            }
            
            # Convert any remaining UUID objects to strings
            response_data = ChatAPIView._convert_uuids_to_strings(response_data)
            
            return response_data
            
        except Exception as e:
            logger.error(f"Failed to process chat message: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise RuntimeError(f"Chat message processing failed: {e}")
    
    @staticmethod
    @api_view(['DELETE'])
    @permission_classes([AllowAny])
    def delete_chat_session(request, session_id):
        """Delete a chat session and all its messages."""
        try:
            if not supabase_client.is_available():
                return Response({
                    'error': 'Database not available'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            client = supabase_client.get_client()
            
            # Delete messages first (due to foreign key constraint)
            client.table('langextract_chat_messages').delete().eq('session_id', session_id).execute()
            
            # Delete session
            response = client.table('langextract_chat_sessions').delete().eq('id', session_id).execute()
            
            if response.data:
                return Response({
                    'success': True,
                    'message': 'Chat session deleted successfully'
                })
            else:
                return Response({
                    'error': 'Chat session not found'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Failed to delete chat session {session_id}: {e}")
            return Response({
                'error': 'Failed to delete chat session',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)