"""
Main processor module that orchestrates schema extraction and embedding generation.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from .schema_extractor import schema_extractor
from .openai_client import openai_client

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Main processor for handling document chunks and generating embeddings."""
    
    def __init__(self):
        self.schema_extractor = schema_extractor
        self.openai_client = openai_client
    
    def process_documents(self, documents: List[Dict[str, Any]], 
                         schemas: List[str], options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process multiple document chunks and generate embeddings.
        
        Args:
            documents: List of document chunks with text and metadata
            schemas: List of schema names to apply
            options: Processing options
            
        Returns:
            Dictionary containing processed documents and summary
        """
        start_time = time.time()
        processed_documents = []
        failed_chunks = 0
        
        for document in documents:
            try:
                processed_doc = self._process_single_document(document, schemas, options)
                if processed_doc:
                    processed_documents.append(processed_doc)
                else:
                    failed_chunks += 1
            except Exception as e:
                logger.error(f"Error processing document {document.get('chunk_id', 'unknown')}: {e}")
                failed_chunks += 1
        
        total_processing_time = time.time() - start_time
        
        return {
            'status': 'success',
            'processed_documents': processed_documents,
            'summary': {
                'total_chunks': len(documents),
                'processed_chunks': len(processed_documents),
                'failed_chunks': failed_chunks,
                'total_processing_time': round(total_processing_time, 3)
            }
        }
    
    def _process_single_document(self, document: Dict[str, Any], 
                                 schemas: List[str], options: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single document chunk.
        
        Args:
            document: Document chunk with text and metadata
            schemas: List of schema names to apply
            options: Processing options
            
        Returns:
            Processed document with extracted data and embeddings
        """
        text = document.get('text', '')
        chunk_id = document.get('chunk_id', 'unknown')
        document_id = document.get('document_id', 'unknown')
        
        if not text:
            logger.warning(f"Empty text for chunk {chunk_id}")
            return None
        
        # Validate text length for OpenAI
        if not self.openai_client.validate_text_length(text):
            logger.warning(f"Text too long for chunk {chunk_id}, truncating")
            text = self.openai_client.truncate_text(text)
        
        # Extract schema-based data
        extraction_result = self.schema_extractor.extract_from_chunk(text, schemas, options)
        
        # Generate embeddings
        embeddings = self._generate_embeddings(text, extraction_result['extracted_data'])
        
        # Combine results
        processed_document = {
            'chunk_id': chunk_id,
            'document_id': document_id,
            'original_text': document.get('text', ''),
            'extracted_data': extraction_result['extracted_data'],
            'embeddings': embeddings,
            'metadata': {
                'processing_time': extraction_result['metadata']['processing_time'],
                'schemas_applied': extraction_result['metadata']['schemas_applied'],
                'embedding_model': getattr(self.openai_client, 'model', 'not_configured')
            }
        }
        
        return processed_document
    
    def _generate_embeddings(self, text: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate embeddings for text and extracted data.
        
        Args:
            text: Original text chunk
            extracted_data: Extracted structured data
            
        Returns:
            Dictionary containing various embeddings
        """
        embeddings = {}
        
        # Generate embedding for the original text
        text_embedding = self.openai_client.generate_embedding(text)
        if text_embedding:
            embeddings['text'] = text_embedding
        
        # Generate embeddings for schema matches
        schema_embeddings = {}
        for schema_name, schema_data in extracted_data.get('schema_matches', {}).items():
            if schema_data:
                # Create a summary string for the schema data
                schema_summary = self._create_schema_summary(schema_name, schema_data)
                schema_embedding = self.openai_client.generate_embedding(schema_summary)
                if schema_embedding:
                    schema_embeddings[schema_name] = schema_embedding
        
        if schema_embeddings:
            embeddings['schemas'] = schema_embeddings
        
        # Generate embeddings for key phrases
        key_phrases = extracted_data.get('key_phrases', [])
        if key_phrases:
            phrase_embeddings = {}
            for phrase in key_phrases[:3]:  # Limit to 3 phrases
                phrase_embedding = self.openai_client.generate_embedding(phrase)
                if phrase_embedding:
                    phrase_embeddings[phrase] = phrase_embedding
            
            if phrase_embeddings:
                embeddings['key_phrases'] = phrase_embeddings
        
        return embeddings
    
    def _create_schema_summary(self, schema_name: str, schema_data: Dict[str, Any]) -> str:
        """
        Create a summary string from schema data for embedding generation.
        
        Args:
            schema_name: Name of the schema
            schema_data: Extracted data from the schema
            
        Returns:
            Summary string for embedding
        """
        summary_parts = [f"Schema: {schema_name}"]
        
        for field_name, field_value in schema_data.items():
            if field_value:  # Only include non-empty values
                if isinstance(field_value, list):
                    summary_parts.append(f"{field_name}: {', '.join(map(str, field_value))}")
                else:
                    summary_parts.append(f"{field_name}: {field_value}")
        
        return "; ".join(summary_parts)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about the processing system."""
        stats = {
            'available_schemas': self.schema_extractor.schema_loader.list_schemas(),
            'available_vocabularies': self.schema_extractor.schema_loader.list_vocabularies()
        }
        
        # Add OpenAI info if available
        if hasattr(self.openai_client, 'get_model_info'):
            try:
                stats['openai_model'] = self.openai_client.get_model_info()
            except Exception as e:
                logger.warning(f"Could not get OpenAI model info: {e}")
                stats['openai_model'] = {'status': 'not_available'}
        
        return stats
    
    def test_system(self) -> Dict[str, Any]:
        """Test the entire processing system."""
        test_results = {
            'openai_connection': False,
            'schema_loading': False,
            'text_processing': False
        }
        
        # Test OpenAI connection
        try:
            test_results['openai_connection'] = self.openai_client.test_connection()
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
        
        # Test schema loading
        try:
            schemas = self.schema_extractor.schema_loader.list_schemas()
            test_results['schema_loading'] = len(schemas) > 0
        except Exception as e:
            logger.error(f"Schema loading test failed: {e}")
        
        # Test text processing
        try:
            test_text = "This is a test document with some content."
            test_schemas = ['contract_terms']
            test_options = {'extract_entities': True, 'extract_categories': True}
            
            result = self.schema_extractor.extract_from_chunk(test_text, test_schemas, test_options)
            test_results['text_processing'] = result is not None
        except Exception as e:
            logger.error(f"Text processing test failed: {e}")
        
        return test_results


# Global document processor instance
document_processor = DocumentProcessor()
