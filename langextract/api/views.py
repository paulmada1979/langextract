"""
API views for document processing and system management.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .serializers import (
    DocumentProcessingRequestSerializer,
    DocumentProcessingResponseSerializer,
    SystemStatusSerializer
)
from core.processor import document_processor
from core.schema_loader import schema_loader

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(['POST'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def process_documents(request):
    """
    Process document chunks and generate embeddings.
    
    POST /api/process/
    """
    try:
        # Validate request data
        serializer = DocumentProcessingRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Invalid request data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract validated data
        documents = serializer.validated_data['documents']
        schemas = serializer.validated_data['schemas']
        options = serializer.validated_data.get('options', {})
        
        # Validate schemas exist
        available_schemas = schema_loader.list_schemas()
        invalid_schemas = [s for s in schemas if s not in available_schemas]
        if invalid_schemas:
            return Response({
                'status': 'error',
                'message': f'Invalid schemas: {", ".join(invalid_schemas)}',
                'available_schemas': available_schemas
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process documents
        logger.info(f"Processing {len(documents)} documents with schemas: {schemas}")
        result = document_processor.process_documents(documents, schemas, options)
        
        # Validate response data
        response_serializer = DocumentProcessingResponseSerializer(data=result)
        if not response_serializer.is_valid():
            logger.error(f"Response validation failed: {response_serializer.errors}")
            return Response({
                'status': 'error',
                'message': 'Internal processing error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error processing documents: {e}")
        return Response({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
def list_schemas(request):
    """
    List all available schemas.
    
    GET /api/schemas/
    """
    try:
        schemas = schema_loader.list_schemas()
        vocabularies = schema_loader.list_vocabularies()
        registry = schema_loader.get_registry()
        
        return Response({
            'status': 'success',
            'schemas': schemas,
            'vocabularies': vocabularies,
            'registry': registry
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing schemas: {e}")
        return Response({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
def get_schema(request, schema_name):
    """
    Get details of a specific schema.
    
    GET /api/schemas/{schema_name}/
    """
    try:
        schema = schema_loader.get_schema(schema_name)
        if not schema:
            return Response({
                'status': 'error',
                'message': f'Schema "{schema_name}" not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'status': 'success',
            'schema': schema
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting schema {schema_name}: {e}")
        return Response({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
def system_status(request):
    """
    Get system status and health information.
    
    GET /api/status/
    """
    try:
        # Test system components
        test_results = document_processor.test_system()
        
        # Get processing stats
        stats = document_processor.get_processing_stats()
        
        # Determine overall status - consider it healthy if core functionality works
        core_functionality = test_results['schema_loading'] and test_results['text_processing']
        overall_status = 'healthy' if core_functionality else 'degraded'
        
        response_data = {
            'status': overall_status,
            'openai_connection': test_results['openai_connection'],
            'schema_loading': test_results['schema_loading'],
            'text_processing': test_results['text_processing'],
            'available_schemas': stats['available_schemas'],
            'openai_model': stats.get('openai_model', {})
        }
        
        # Validate response
        serializer = SystemStatusSerializer(data=response_data)
        if not serializer.is_valid():
            logger.error(f"Status response validation failed: {serializer.errors}")
            return Response({
                'status': 'error',
                'message': 'Internal validation error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return Response({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
def processing_stats(request):
    """
    Get processing statistics and system information.
    
    GET /api/stats/
    """
    try:
        stats = document_processor.get_processing_stats()
        
        return Response({
            'status': 'success',
            'stats': stats
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting processing stats: {e}")
        return Response({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
