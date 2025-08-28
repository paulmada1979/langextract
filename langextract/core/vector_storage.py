"""
Vector storage service for managing embeddings in Supabase.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from .supabase_client import supabase_client

logger = logging.getLogger(__name__)


class VectorStorage:
    """Service for storing and retrieving embeddings from Supabase vector database."""
    
    def __init__(self):
        """Initialize vector storage service."""
        self.table_name = 'embeddings'
        self._client = None
    
    def _get_client(self):
        """Get Supabase client, checking if it's available."""
        if not self._client:
            if not supabase_client.is_available():
                raise RuntimeError("Supabase client not available. Check your environment variables.")
            self._client = supabase_client.get_client()
        return self._client
    
    def store_embeddings(self, document_data: Dict[str, Any]) -> Optional[str]:
        """
        Store embeddings for a document chunk.
        
        Args:
            document_data: Document data containing embeddings and metadata
            
        Returns:
            ID of the stored embedding record
        """
        try:
            # Prepare embedding data for storage
            embedding_record = self._prepare_embedding_record(document_data)
            
            # Insert into Supabase
            client = self._get_client()
            response = client.table(self.table_name).insert(embedding_record).execute()
            
            if response.data:
                embedding_id = response.data[0]['id']
                logger.info(f"Stored embeddings for chunk {document_data.get('chunk_id')} with ID: {embedding_id}")
                return embedding_id
            else:
                logger.error("No data returned from embedding insertion")
                return None
                
        except Exception as e:
            logger.error(f"Failed to store embeddings for chunk {document_data.get('chunk_id')}: {e}")
            return None
    
    def store_batch_embeddings(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Store embeddings for multiple documents in batch.
        
        Args:
            documents: List of document data
            
        Returns:
            Dictionary with storage results
        """
        results = {
            'successful': 0,
            'failed': 0,
            'stored_ids': []
        }
        
        for document in documents:
            try:
                embedding_id = self.store_embeddings(document)
                if embedding_id:
                    results['successful'] += 1
                    results['stored_ids'].append(embedding_id)
                else:
                    results['failed'] += 1
            except Exception as e:
                logger.error(f"Failed to store embeddings for document: {e}")
                results['failed'] += 1
        
        logger.info(f"Batch storage completed: {results['successful']} successful, {results['failed']} failed")
        return results
    
    def search_similar_embeddings(self, query_embedding: List[float], 
                                 limit: int = 10, 
                                 similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of similar documents
        """
        try:
            # Use pgvector's cosine similarity for search
            client = self._get_client()
            response = client.rpc(
                'match_embeddings',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': similarity_threshold,
                    'match_count': limit
                }
            ).execute()
            
            if response.data:
                logger.info(f"Found {len(response.data)} similar embeddings")
                return response.data
            else:
                logger.info("No similar embeddings found")
                return []
                
        except Exception as e:
            logger.error(f"Failed to search embeddings: {e}")
            return []
    
    def get_embedding_by_id(self, embedding_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve embedding by ID.
        
        Args:
            embedding_id: ID of the embedding record
            
        Returns:
            Embedding data or None if not found
        """
        try:
            client = self._get_client()
            response = client.table(self.table_name).select('*').eq('id', embedding_id).execute()
            
            if response.data:
                return response.data[0]
            else:
                logger.warning(f"No embedding found with ID: {embedding_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve embedding {embedding_id}: {e}")
            return None
    
    def delete_embedding(self, embedding_id: str) -> bool:
        """
        Delete an embedding record.
        
        Args:
            embedding_id: ID of the embedding record
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = self._get_client()
            response = client.table(self.table_name).delete().eq('id', embedding_id).execute()
            
            if response.data:
                logger.info(f"Deleted embedding with ID: {embedding_id}")
                return True
            else:
                logger.warning(f"No embedding found to delete with ID: {embedding_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete embedding {embedding_id}: {e}")
            return False
    
    def _prepare_embedding_record(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare document data for storage in the embeddings table.
        
        Args:
            document_data: Raw document data
            
        Returns:
            Formatted embedding record
        """
        embeddings = document_data.get('embeddings', {})
        
        # Get the main text embedding (primary vector for similarity search)
        text_embedding = embeddings.get('text', [])
        
        # Prepare the record
        record = {
            'chunk_id': document_data.get('chunk_id'),
            'document_id': document_data.get('document_id'),
            'original_text': document_data.get('original_text', ''),
            'text_embedding': text_embedding,
            'all_embeddings': json.dumps(embeddings),  # Store all embeddings as JSON
            'extracted_data': json.dumps(document_data.get('extracted_data', {})),
            'metadata': json.dumps(document_data.get('metadata', {})),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        return record
    
    def is_available(self) -> bool:
        """Check if vector storage is available."""
        try:
            return supabase_client.is_available()
        except Exception:
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about stored embeddings."""
        try:
            if not self.is_available():
                return {
                    'total_embeddings': 0,
                    'recent_embeddings': [],
                    'status': 'not_configured',
                    'message': 'Supabase not configured'
                }
            
            # Count total embeddings
            client = self._get_client()
            count_response = client.table(self.table_name).select('id', count='exact').execute()
            total_count = count_response.count if hasattr(count_response, 'count') else 0
            
            # Get recent embeddings
            recent_response = client.table(self.table_name).select('created_at').order('created_at', desc=True).limit(5).execute()
            recent_dates = [item['created_at'] for item in recent_response.data] if recent_response.data else []
            
            return {
                'total_embeddings': total_count,
                'recent_embeddings': recent_dates,
                'status': 'connected'
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {
                'total_embeddings': 0,
                'recent_embeddings': [],
                'status': 'error',
                'error': str(e)
            }


# Global vector storage instance
try:
    vector_storage = VectorStorage()
except Exception as e:
    logger.warning(f"Failed to initialize vector storage: {e}")
    # Create a dummy vector storage that always returns False for is_available
    class DummyVectorStorage:
        def is_available(self):
            return False
        def store_embeddings(self, *args, **kwargs):
            return None
        def store_batch_embeddings(self, *args, **kwargs):
            return {'status': 'not_available', 'message': 'Vector storage not available', 'stored': 0, 'failed': 0}
        def search_similar_embeddings(self, *args, **kwargs):
            return []
        def get_embedding_by_id(self, *args, **kwargs):
            return None
        def delete_embedding(self, *args, **kwargs):
            return False
        def get_storage_stats(self):
            return {'status': 'not_available', 'message': 'Vector storage not available'}
    
    vector_storage = DummyVectorStorage()
