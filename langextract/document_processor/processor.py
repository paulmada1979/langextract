"""
Main document processor for handling file uploads and processing pipeline.
"""

import os
import uuid
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Optional imports with fallbacks
try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False
    aiofiles = None

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import PipelineOptions
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    DocumentConverter = None
    PipelineOptions = None

from .chunker import DocumentChunker
from .extractor import MetadataExtractor
from core.supabase_client import supabase_client
from core.openai_client import openai_client

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Main document processor that handles the complete pipeline:
    1. File upload and validation
    2. Document extraction using docling
    3. Chunking for optimal processing
    4. Metadata extraction using langextract
    5. Embedding generation and storage
    """
    
    def __init__(self, upload_dir: str = "uploads", max_file_size: int = 50 * 1024 * 1024):
        """
        Initialize the document processor.
        
        Args:
            upload_dir: Directory to store uploaded files
            max_file_size: Maximum file size in bytes (default: 50MB)
        """
        self.upload_dir = Path(upload_dir)
        self.max_file_size = max_file_size
        self.supported_formats = {'.pdf', '.docx', '.doc', '.md', '.txt'}
        
        # Initialize components
        self.chunker = DocumentChunker()
        self.extractor = MetadataExtractor()
        
        # Initialize docling converter
        self.converter = self._init_docling_converter()
        
        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DocumentProcessor initialized with upload_dir: {self.upload_dir}")
    
    def _init_docling_converter(self) -> Optional[DocumentConverter]:
        """Initialize docling document converter with optimized settings."""
        if not DOCLING_AVAILABLE:
            logger.warning("Docling not available - document processing will be limited")
            return None
            
        try:
            # Create converter with default settings
            # Note: The new docling API doesn't require complex configuration
            converter = DocumentConverter()
            
            logger.info("Docling converter initialized successfully")
            return converter
            
        except Exception as e:
            logger.error(f"Failed to initialize docling converter: {e}")
            return None
    
    async def process_document(self, file_data: bytes, filename: str, 
                             user_id: str, schemas: List[str] = None) -> Dict[str, Any]:
        """
        Process a document through the complete pipeline.
        
        Args:
            file_data: Raw file data
            filename: Original filename
            schemas: List of schemas to apply for metadata extraction
            
        Returns:
            Dictionary with processing results
        """
        document_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        try:
            # Validate file
            file_info = self._validate_file(file_data, filename)
            
            # Store file
            file_path = await self._store_file(file_data, filename, document_id)
            
            # Create document record in database
            doc_record = await self._create_document_record(
                document_id, filename, file_info, file_path, user_id
            )
            
            # Extract content using docling
            logger.info(f"Extracting content from {filename} using docling")
            extracted_content = await self._extract_content(file_path, file_info['file_type'])
            
            # Chunk the document
            logger.info(f"Chunking document {document_id}")
            chunks = await self._chunk_document(extracted_content, document_id)
            
            # Process chunks with metadata extraction and embeddings
            logger.info(f"Processing {len(chunks)} chunks for document {document_id}")
            processed_chunks = await self._process_chunks(
                chunks, document_id, schemas or ['invoice', 'support_case']
            )
            
            # Store processed chunks in database
            await self._store_processed_chunks(processed_chunks, document_id, user_id)
            
            # Extract and aggregate metadata from all chunks
            document_metadata = await self._aggregate_document_metadata(processed_chunks)
            
            # Update document status and metadata
            await self._update_document_status(document_id, 'completed', metadata=document_metadata)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                'document_id': document_id,
                'filename': filename,
                'status': 'completed',
                'chunks_processed': len(processed_chunks),
                'processing_time': processing_time,
                'file_info': file_info,
                'chunks': processed_chunks[:5]  # Return first 5 chunks as preview
            }
            
            logger.info(f"Successfully processed document {document_id} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {e}")
            await self._update_document_status(document_id, 'failed', str(e))
            raise RuntimeError(f"Document processing failed: {e}")
    
    def _validate_file(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Validate uploaded file."""
        # Check file size
        if len(file_data) > self.max_file_size:
            raise ValueError(f"File size {len(file_data)} exceeds maximum {self.max_file_size}")
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_ext}. Supported: {self.supported_formats}")
        
        return {
            'file_type': file_ext[1:],  # Remove the dot
            'file_size': len(file_data),
            'original_filename': filename
        }
    
    async def _store_file(self, file_data: bytes, filename: str, document_id: str) -> str:
        """Store uploaded file to disk."""
        # Create safe filename
        safe_filename = f"{document_id}_{filename}"
        file_path = self.upload_dir / safe_filename
        
        # Write file asynchronously if aiofiles is available, otherwise synchronously
        if AIOFILES_AVAILABLE:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_data)
        else:
            # Fallback to synchronous file writing
            with open(file_path, 'wb') as f:
                f.write(file_data)
        
        logger.info(f"Stored file {filename} as {file_path}")
        return str(file_path)
    
    async def _create_document_record(self, document_id: str, filename: str, 
                                    file_info: Dict[str, Any], file_path: str, user_id: str) -> Dict[str, Any]:
        """Create document record in database."""
        try:
            if not supabase_client.is_available():
                logger.warning("Supabase not available, skipping database record creation")
                return {'id': document_id}
            
            client = supabase_client.get_client()
            
            doc_data = {
                'id': document_id,
                'user_id': user_id,
                'filename': filename,
                'original_filename': file_info['original_filename'],
                'file_type': file_info['file_type'],
                'file_size': file_info['file_size'],
                'file_path': file_path,
                'upload_status': 'uploaded',
                'processing_status': 'processing',
                'metadata': {}
            }
            
            response = client.table('langextract_documents').insert(doc_data).execute()
            
            if response.data:
                logger.info(f"Created document record for {document_id}")
                return response.data[0]
            else:
                raise RuntimeError("Failed to create document record")
                
        except Exception as e:
            logger.error(f"Failed to create document record: {e}")
            raise
    
    async def _extract_content(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Extract content from document using docling."""
        if not DOCLING_AVAILABLE or not self.converter:
            # Fallback to simple text extraction
            logger.warning("Docling not available, using fallback text extraction")
            return self._fallback_text_extraction(file_path, file_type)
            
        try:
            # Run docling conversion in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._run_docling_conversion, file_path
            )
            
            # Process the result
            content = self._process_docling_result(result)
            
            logger.info(f"Extracted content from {file_path}: {len(content.get('text', ''))} chars")
            return content
            
        except Exception as e:
            logger.error(f"Failed to extract content from {file_path}: {e}")
            # Fallback to simple text extraction
            return self._fallback_text_extraction(file_path, file_type)
    
    def _run_docling_conversion(self, file_path: str):
        """Run docling conversion (synchronous)."""
        if self.converter:
            return self.converter.convert(file_path)
        return None
    
    def _fallback_text_extraction(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Fallback text extraction when docling is not available."""
        content = {
            'text': '',
            'tables': [],
            'images': [],
            'metadata': {}
        }
        
        try:
            if file_type.lower() == 'txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content['text'] = f.read()
            elif file_type.lower() == 'md':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content['text'] = f.read()
            else:
                # For other file types, we'll need to implement basic extraction
                # For now, just return empty content
                content['text'] = f"[File type {file_type} not supported without docling]"
                logger.warning(f"File type {file_type} requires docling for proper extraction")
                
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            content['text'] = f"[Error extracting content: {str(e)}]"
        
        return content
    
    def _process_docling_result(self, result) -> Dict[str, Any]:
        """Process docling conversion result."""
        content = {
            'text': '',
            'tables': [],
            'images': [],
            'metadata': {}
        }
        
        try:
            # Extract main text from the result
            if hasattr(result, 'document') and result.document:
                doc = result.document
                
                # Get main text content
                if hasattr(doc, 'text') and doc.text:
                    content['text'] = doc.text
                elif hasattr(doc, 'export_to_markdown'):
                    # Try to get text via markdown export
                    content['text'] = doc.export_to_markdown()
                
                # Extract tables if available
                if hasattr(doc, 'tables') and doc.tables:
                    for table in doc.tables:
                        table_data = {
                            'content': str(table),
                            'metadata': getattr(table, 'metadata', {})
                        }
                        content['tables'].append(table_data)
                
                # Extract images if available
                if hasattr(doc, 'images') and doc.images:
                    for image in doc.images:
                        image_data = {
                            'content': str(image),
                            'metadata': getattr(image, 'metadata', {})
                        }
                        content['images'].append(image_data)
                
                # Extract metadata
                if hasattr(doc, 'metadata') and doc.metadata:
                    content['metadata'] = doc.metadata
            else:
                # If no document attribute, try to get text directly from result
                if hasattr(result, 'text') and result.text:
                    content['text'] = result.text
                elif hasattr(result, 'export_to_markdown'):
                    content['text'] = result.export_to_markdown()
                
        except Exception as e:
            logger.warning(f"Error processing docling result: {e}")
        
        return content
    
    async def _chunk_document(self, content: Dict[str, Any], document_id: str) -> List[Dict[str, Any]]:
        """Chunk the extracted document content."""
        try:
            chunks = await self.chunker.chunk_content(content, document_id)
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk document {document_id}: {e}")
            raise RuntimeError(f"Document chunking failed: {e}")
    
    async def _process_chunks(self, chunks: List[Dict[str, Any]], document_id: str, 
                            schemas: List[str]) -> List[Dict[str, Any]]:
        """Process chunks with metadata extraction and embedding generation."""
        processed_chunks = []
        
        for i, chunk in enumerate(chunks):
            try:
                # Extract metadata using langextract
                extracted_metadata = await self.extractor.extract_metadata(
                    chunk['content'], schemas
                )
                
                # Generate embeddings
                embeddings = await self._generate_embeddings(chunk['content'])
                
                # Combine all data
                processed_chunk = {
                    'id': str(uuid.uuid4()),
                    'document_id': document_id,
                    'chunk_id': chunk['chunk_id'],
                    'chunk_index': i,
                    'content': chunk['content'],
                    'content_type': chunk.get('content_type', 'text'),
                    'chunk_metadata': chunk.get('metadata', {}),
                    'extracted_metadata': extracted_metadata,
                    'embeddings': embeddings,
                    'created_at': datetime.utcnow().isoformat()
                }
                
                processed_chunks.append(processed_chunk)
                
            except Exception as e:
                logger.error(f"Failed to process chunk {i} for document {document_id}: {e}")
                # Continue processing other chunks
                continue
        
        return processed_chunks
    
    async def _aggregate_document_metadata(self, processed_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate metadata from all processed chunks into document-level metadata."""
        try:
            aggregated_metadata = {
                'total_chunks': len(processed_chunks),
                'document_type_indicators': {},
                'key_entities': [],
                'content_insights': {
                    'total_text_length': 0,
                    'average_chunk_length': 0,
                    'document_sections': [],
                    'action_items': []
                },
                'extraction_summary': {
                    'successful_extractions': 0,
                    'failed_extractions': 0,
                    'schemas_applied': set()
                }
            }
            
            # Aggregate data from all chunks
            all_entities = []
            all_sections = []
            all_action_items = []
            total_text_length = 0
            successful_extractions = 0
            
            for chunk in processed_chunks:
                # Sum text length
                chunk_text_length = len(chunk.get('content', ''))
                total_text_length += chunk_text_length
                
                # Extract metadata from chunk
                extracted_metadata = chunk.get('extracted_metadata', {})
                
                if extracted_metadata and not extracted_metadata.get('error'):
                    successful_extractions += 1
                    
                    # Aggregate document type indicators
                    langextract_result = extracted_metadata.get('langextract_result', {})
                    if langextract_result:
                        # This would contain schema-specific extracted data
                        pass
                    
                    # Aggregate entities
                    content_insights = extracted_metadata.get('content_insights', {})
                    if content_insights:
                        entities = content_insights.get('important_entities', [])
                        all_entities.extend(entities)
                        
                        sections = content_insights.get('document_sections', [])
                        all_sections.extend(sections)
                        
                        action_items = content_insights.get('action_items', [])
                        all_action_items.extend(action_items)
                    
                    # Track schemas applied
                    text_analysis = extracted_metadata.get('text_analysis', {})
                    doc_type_indicators = text_analysis.get('document_type_indicators', {})
                    if doc_type_indicators:
                        likely_types = doc_type_indicators.get('likely_types', [])
                        for doc_type in likely_types:
                            aggregated_metadata['extraction_summary']['schemas_applied'].add(doc_type)
            
            # Calculate averages and limits
            aggregated_metadata['content_insights']['total_text_length'] = total_text_length
            aggregated_metadata['content_insights']['average_chunk_length'] = total_text_length / len(processed_chunks) if processed_chunks else 0
            
            # Limit and deduplicate aggregated data
            aggregated_metadata['key_entities'] = self._deduplicate_entities(all_entities)[:20]  # Top 20 entities
            aggregated_metadata['content_insights']['document_sections'] = all_sections[:10]  # Top 10 sections
            aggregated_metadata['content_insights']['action_items'] = all_action_items[:10]  # Top 10 action items
            
            # Update extraction summary
            aggregated_metadata['extraction_summary']['successful_extractions'] = successful_extractions
            aggregated_metadata['extraction_summary']['failed_extractions'] = len(processed_chunks) - successful_extractions
            aggregated_metadata['extraction_summary']['schemas_applied'] = list(aggregated_metadata['extraction_summary']['schemas_applied'])
            
            # Determine primary document type
            if aggregated_metadata['extraction_summary']['schemas_applied']:
                # Use the most frequently detected document type
                type_counts = {}
                for chunk in processed_chunks:
                    extracted_metadata = chunk.get('extracted_metadata', {})
                    text_analysis = extracted_metadata.get('text_analysis', {})
                    doc_type_indicators = text_analysis.get('document_type_indicators', {})
                    likely_types = doc_type_indicators.get('likely_types', [])
                    for doc_type in likely_types:
                        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
                
                if type_counts:
                    primary_type = max(type_counts.items(), key=lambda x: x[1])[0]
                    aggregated_metadata['document_type_indicators']['primary_type'] = primary_type
                    aggregated_metadata['document_type_indicators']['confidence_scores'] = type_counts
            
            logger.info(f"Aggregated metadata from {len(processed_chunks)} chunks")
            return aggregated_metadata
            
        except Exception as e:
            logger.error(f"Failed to aggregate document metadata: {e}")
            return {'error': str(e), 'total_chunks': len(processed_chunks)}
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate entities based on text content."""
        seen_entities = set()
        deduplicated = []
        
        for entity in entities:
            entity_text = entity.get('text', '').lower().strip()
            if entity_text and entity_text not in seen_entities:
                seen_entities.add(entity_text)
                deduplicated.append(entity)
        
        return deduplicated
    
    async def _generate_embeddings(self, text: str) -> Dict[str, List[float]]:
        """Generate embeddings for text content."""
        try:
            if not openai_client.is_available():
                logger.warning("OpenAI client not available, skipping embeddings")
                return {}
            
            # Generate main text embedding
            text_embedding = openai_client.generate_embedding(text)
            
            # Validate embedding
            if not text_embedding or len(text_embedding) == 0:
                logger.warning("Generated embedding is empty, skipping")
                return {}
            
            # Ensure embedding has the expected dimension (1536 for text-embedding-3-small)
            if len(text_embedding) != 1536:
                logger.warning(f"Embedding dimension mismatch: expected 1536, got {len(text_embedding)}")
                return {}
            
            embeddings = {
                'text': text_embedding
            }
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return {}
    
    async def _store_processed_chunks(self, chunks: List[Dict[str, Any]], document_id: str, user_id: str):
        """Store processed chunks in database."""
        try:
            if not supabase_client.is_available():
                logger.warning("Supabase not available, skipping chunk storage")
                return
            
            client = supabase_client.get_client()
            
            # Prepare data for batch insert
            chunk_records = []
            for chunk in chunks:
                # Get text embedding, but only if it's valid
                text_embedding = chunk['embeddings'].get('text', [])
                
                # Skip chunks with invalid embeddings
                if not text_embedding or len(text_embedding) == 0 or len(text_embedding) != 1536:
                    logger.warning(f"Skipping chunk {chunk['chunk_id']} due to invalid embedding")
                    continue
                
                record = {
                    'id': chunk['id'],
                    'user_id': user_id,
                    'document_id': chunk['document_id'],
                    'chunk_id': chunk['chunk_id'],
                    'chunk_index': chunk['chunk_index'],
                    'content': chunk['content'],
                    'content_type': chunk['content_type'],
                    'embedding': text_embedding,
                    'all_embeddings': chunk['embeddings'],
                    'extracted_metadata': chunk['extracted_metadata'],
                    'chunk_metadata': chunk['chunk_metadata']
                }
                chunk_records.append(record)
            
            # Batch insert only if we have valid chunks
            if chunk_records:
                response = client.table('langextract_processed_embeddings').insert(chunk_records).execute()
                
                if response.data:
                    logger.info(f"Stored {len(chunk_records)} chunks for document {document_id}")
                else:
                    raise RuntimeError("Failed to store processed chunks")
            else:
                logger.warning(f"No valid chunks to store for document {document_id} (all embeddings were invalid)")
                raise RuntimeError("No valid chunks with embeddings to store")
                
        except Exception as e:
            logger.error(f"Failed to store processed chunks: {e}")
            raise
    
    async def _update_document_status(self, document_id: str, status: str, error: str = None, metadata: Dict[str, Any] = None):
        """Update document processing status and metadata."""
        try:
            if not supabase_client.is_available():
                logger.warning("Supabase not available, skipping status update")
                return
            
            client = supabase_client.get_client()
            
            update_data = {
                'processing_status': status,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if status == 'completed':
                update_data['processed_at'] = datetime.utcnow().isoformat()
                # Update metadata if provided
                if metadata:
                    update_data['metadata'] = metadata
            elif status == 'failed' and error:
                update_data['processing_error'] = error
            
            response = client.table('langextract_documents').update(update_data).eq('id', document_id).execute()
            
            if response.data:
                logger.info(f"Updated document {document_id} status to {status}")
                if metadata:
                    logger.info(f"Updated document {document_id} metadata with {len(metadata)} fields")
            else:
                logger.warning(f"Failed to update document {document_id} status")
                
        except Exception as e:
            logger.error(f"Failed to update document status: {e}")
    
    async def get_document_status(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document processing status."""
        try:
            if not supabase_client.is_available():
                return None
            
            client = supabase_client.get_client()
            response = client.table('langextract_documents').select('*').eq('id', document_id).execute()
            
            if response.data:
                return response.data[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get document status: {e}")
            return None
    
    async def list_documents(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List uploaded documents."""
        try:
            if not supabase_client.is_available():
                return []
            
            client = supabase_client.get_client()
            response = client.table('langextract_documents').select('*').order('created_at', desc=True).range(offset, offset + limit - 1).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks."""
        try:
            if not supabase_client.is_available():
                return False
            
            client = supabase_client.get_client()
            
            # Delete chunks first (due to foreign key constraint)
            client.table('langextract_processed_embeddings').delete().eq('document_id', document_id).execute()
            
            # Delete document
            response = client.table('langextract_documents').delete().eq('id', document_id).execute()
            
            if response.data:
                logger.info(f"Deleted document {document_id}")
                return True
            else:
                logger.warning(f"Document {document_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
