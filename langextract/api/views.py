"""
API views for the langextract service.
"""

import logging
from datetime import datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from core.processor import document_processor
from core.vector_storage import vector_storage

logger = logging.getLogger(__name__)


@api_view(['POST'])
def extract_schemas(request):
    """Extract schemas from document chunks."""
    try:
        data = request.data
        documents = data.get('documents', [])
        schemas = data.get('schemas', [])
        options = data.get('options', {})
        
        if not documents or not schemas:
            return Response(
                {'error': 'Documents and schemas are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process documents and store embeddings
        result = document_processor.process_documents(documents, schemas, options)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in extract_schemas: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def list_schemas(request):
    """List available schemas."""
    try:
        schemas = document_processor.schema_extractor.schema_loader.list_schemas()
        vocabularies = document_processor.schema_extractor.schema_loader.list_vocabularies()
        
        return Response({
            'schemas': schemas,
            'vocabularies': vocabularies
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in list_schemas: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def system_status(request):
    """Get system status and health check."""
    try:
        # Test core system
        core_status = document_processor.test_system()
        
        # Test vector storage
        vector_status = document_processor.get_vector_storage_stats()
        
        return Response({
            'core_system': core_status,
            'vector_storage': vector_status,
            'status': 'healthy' if core_status.get('text_processing') else 'degraded'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in system_status: {e}")
        return Response(
            {'error': str(e), 'status': 'unhealthy'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def health_check(request):
    """Simple health check endpoint that doesn't require external services."""
    return Response({
        'status': 'healthy',
        'message': 'Langextract service is running',
        'timestamp': datetime.now().isoformat()
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def search_similar_documents(request):
    """Search for similar documents using vector similarity."""
    try:
        data = request.data
        query_text = data.get('query_text', '')
        limit = data.get('limit', 10)
        similarity_threshold = data.get('similarity_threshold', 0.7)
        
        if not query_text:
            return Response(
                {'error': 'Query text is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Search for similar documents
        similar_documents = document_processor.search_similar_documents(
            query_text, limit, similarity_threshold
        )
        
        return Response({
            'query_text': query_text,
            'similarity_threshold': similarity_threshold,
            'results': similar_documents,
            'total_results': len(similar_documents)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in search_similar_documents: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_embedding_by_id(request, embedding_id):
    """Retrieve embedding by ID."""
    try:
        embedding = vector_storage.get_embedding_by_id(embedding_id)
        
        if not embedding:
            return Response(
                {'error': 'Embedding not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(embedding, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in get_embedding_by_id: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def delete_embedding(request, embedding_id):
    """Delete embedding by ID."""
    try:
        success = vector_storage.delete_embedding(embedding_id)
        
        if not success:
            return Response(
                {'error': 'Embedding not found or could not be deleted'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'message': f'Embedding {embedding_id} deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in delete_embedding: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def vector_storage_stats(request):
    """Get vector storage statistics."""
    try:
        stats = vector_storage.get_storage_stats()
        return Response(stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in vector_storage_stats: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
