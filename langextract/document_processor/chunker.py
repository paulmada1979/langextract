"""
Document chunker for optimal text splitting and processing.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import uuid

logger = logging.getLogger(__name__)


@dataclass
class ChunkConfig:
    """Configuration for document chunking."""
    max_chunk_size: int = 1000  # Maximum characters per chunk
    min_chunk_size: int = 200   # Minimum characters per chunk
    overlap_size: int = 100     # Overlap between chunks
    preserve_sentences: bool = True  # Try to preserve sentence boundaries
    preserve_paragraphs: bool = True  # Try to preserve paragraph boundaries


class DocumentChunker:
    """
    Optimized document chunker that handles different content types
    and ensures optimal chunk sizes for processing.
    """
    
    def __init__(self, config: ChunkConfig = None):
        """
        Initialize the document chunker.
        
        Args:
            config: Chunking configuration
        """
        self.config = config or ChunkConfig()
        logger.info(f"DocumentChunker initialized with config: {self.config}")
    
    async def chunk_content(self, content: Dict[str, Any], document_id: str) -> List[Dict[str, Any]]:
        """
        Chunk document content into optimal pieces.
        
        Args:
            content: Extracted document content
            document_id: Document identifier
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        
        try:
            # Process main text content
            if content.get('text'):
                text_chunks = await self._chunk_text(content['text'], document_id, 'text')
                chunks.extend(text_chunks)
            
            # Process tables separately
            if content.get('tables'):
                for i, table in enumerate(content['tables']):
                    table_chunks = await self._chunk_table(table, document_id, i)
                    chunks.extend(table_chunks)
            
            # Process images (store as metadata chunks)
            if content.get('images'):
                for i, image in enumerate(content['images']):
                    image_chunk = await self._create_image_chunk(image, document_id, i)
                    chunks.append(image_chunk)
            
            # Sort chunks by their position in the document
            chunks.sort(key=lambda x: x.get('chunk_index', 0))
            
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk content for document {document_id}: {e}")
            raise RuntimeError(f"Content chunking failed: {e}")
    
    async def _chunk_text(self, text: str, document_id: str, content_type: str) -> List[Dict[str, Any]]:
        """Chunk text content into optimal pieces."""
        if not text or not text.strip():
            return []
        
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Split into paragraphs first
        paragraphs = self._split_into_paragraphs(text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed max size, finalize current chunk
            if (len(current_chunk) + len(paragraph) > self.config.max_chunk_size 
                and current_chunk.strip()):
                
                # Create chunk from current content
                chunk = await self._create_text_chunk(
                    current_chunk.strip(), document_id, content_type, chunk_index
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # Start new chunk with overlap
                current_chunk = self._get_overlap_text(current_chunk) + paragraph
            else:
                current_chunk += paragraph + "\n\n"
        
        # Add final chunk if there's remaining content
        if current_chunk.strip():
            chunk = await self._create_text_chunk(
                current_chunk.strip(), document_id, content_type, chunk_index
            )
            chunks.append(chunk)
        
        # Post-process chunks to ensure optimal sizes
        chunks = await self._optimize_chunk_sizes(chunks, document_id)
        
        return chunks
    
    async def _chunk_table(self, table: Dict[str, Any], document_id: str, table_index: int) -> List[Dict[str, Any]]:
        """Chunk table content."""
        table_content = table.get('content', '')
        table_metadata = table.get('metadata', {})
        
        if not table_content.strip():
            return []
        
        # For tables, we might want to keep them as single chunks or split by rows
        # For now, keep tables as single chunks
        chunk = {
            'chunk_id': f"{document_id}_table_{table_index}",
            'document_id': document_id,
            'chunk_index': 1000 + table_index,  # Place tables after text chunks
            'content': table_content,
            'content_type': 'table',
            'metadata': {
                'table_index': table_index,
                'table_metadata': table_metadata,
                'chunk_type': 'table'
            }
        }
        
        return [chunk]
    
    async def _create_image_chunk(self, image: Dict[str, Any], document_id: str, image_index: int) -> Dict[str, Any]:
        """Create a chunk for image content."""
        image_content = image.get('content', '')
        image_metadata = image.get('metadata', {})
        
        # For images, we store metadata and description
        chunk = {
            'chunk_id': f"{document_id}_image_{image_index}",
            'document_id': document_id,
            'chunk_index': 2000 + image_index,  # Place images after tables
            'content': f"Image {image_index + 1}: {image_content}",
            'content_type': 'image',
            'metadata': {
                'image_index': image_index,
                'image_metadata': image_metadata,
                'chunk_type': 'image'
            }
        }
        
        return chunk
    
    async def _create_text_chunk(self, text: str, document_id: str, content_type: str, chunk_index: int) -> Dict[str, Any]:
        """Create a text chunk with metadata."""
        # Generate unique chunk ID
        chunk_id = f"{document_id}_chunk_{chunk_index:03d}"
        
        # Extract key information from text
        metadata = await self._extract_chunk_metadata(text, chunk_index)
        
        chunk = {
            'chunk_id': chunk_id,
            'document_id': document_id,
            'chunk_index': chunk_index,
            'content': text,
            'content_type': content_type,
            'metadata': metadata
        }
        
        return chunk
    
    async def _extract_chunk_metadata(self, text: str, chunk_index: int) -> Dict[str, Any]:
        """Extract metadata from chunk text."""
        metadata = {
            'chunk_type': 'text',
            'length': len(text),
            'word_count': len(text.split()),
            'chunk_index': chunk_index
        }
        
        # Extract potential headers
        headers = self._extract_headers(text)
        if headers:
            metadata['headers'] = headers
        
        # Extract potential dates
        dates = self._extract_dates(text)
        if dates:
            metadata['dates'] = dates
        
        # Extract potential numbers/amounts
        numbers = self._extract_numbers(text)
        if numbers:
            metadata['numbers'] = numbers
        
        # Extract potential entities (simple pattern matching)
        entities = self._extract_simple_entities(text)
        if entities:
            metadata['entities'] = entities
        
        return metadata
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere with processing
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Normalize line breaks
        text = re.sub(r'\r\n|\r', '\n', text)
        
        return text.strip()
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split by double newlines or paragraph breaks
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Filter out empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of a chunk."""
        if len(text) <= self.config.overlap_size:
            return text
        
        # Try to find a good break point (sentence or word boundary)
        overlap_text = text[-self.config.overlap_size:]
        
        # Find the last sentence boundary
        sentence_end = overlap_text.rfind('.')
        if sentence_end > self.config.overlap_size // 2:
            overlap_text = overlap_text[sentence_end + 1:]
        
        # Find the last word boundary
        word_end = overlap_text.rfind(' ')
        if word_end > 0:
            overlap_text = overlap_text[word_end + 1:]
        
        return overlap_text + " "
    
    async def _optimize_chunk_sizes(self, chunks: List[Dict[str, Any]], document_id: str) -> List[Dict[str, Any]]:
        """Optimize chunk sizes by splitting or merging chunks."""
        optimized_chunks = []
        
        for chunk in chunks:
            content = chunk['content']
            
            # If chunk is too large, split it further
            if len(content) > self.config.max_chunk_size:
                sub_chunks = await self._split_large_chunk(chunk, document_id)
                optimized_chunks.extend(sub_chunks)
            
            # If chunk is too small, try to merge with next chunk
            elif len(content) < self.config.min_chunk_size and optimized_chunks:
                last_chunk = optimized_chunks[-1]
                if (len(last_chunk['content']) + len(content) <= self.config.max_chunk_size):
                    # Merge chunks
                    last_chunk['content'] += "\n\n" + content
                    last_chunk['metadata']['merged_chunks'] = last_chunk['metadata'].get('merged_chunks', 0) + 1
                    continue
            
            optimized_chunks.append(chunk)
        
        # Re-index chunks
        for i, chunk in enumerate(optimized_chunks):
            chunk['chunk_index'] = i
        
        return optimized_chunks
    
    async def _split_large_chunk(self, chunk: Dict[str, Any], document_id: str) -> List[Dict[str, Any]]:
        """Split a large chunk into smaller pieces."""
        content = chunk['content']
        base_chunk_id = chunk['chunk_id']
        base_index = chunk['chunk_index']
        
        # Split by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        sub_chunks = []
        current_chunk = ""
        sub_index = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.config.max_chunk_size and current_chunk:
                # Create sub-chunk
                sub_chunk = {
                    'chunk_id': f"{base_chunk_id}_sub_{sub_index}",
                    'document_id': document_id,
                    'chunk_index': base_index + sub_index * 0.1,  # Decimal indexing for sub-chunks
                    'content': current_chunk.strip(),
                    'content_type': chunk['content_type'],
                    'metadata': {
                        **chunk['metadata'],
                        'parent_chunk': base_chunk_id,
                        'sub_chunk_index': sub_index
                    }
                }
                sub_chunks.append(sub_chunk)
                sub_index += 1
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add final sub-chunk
        if current_chunk.strip():
            sub_chunk = {
                'chunk_id': f"{base_chunk_id}_sub_{sub_index}",
                'document_id': document_id,
                'chunk_index': base_index + sub_index * 0.1,
                'content': current_chunk.strip(),
                'content_type': chunk['content_type'],
                'metadata': {
                    **chunk['metadata'],
                    'parent_chunk': base_chunk_id,
                    'sub_chunk_index': sub_index
                }
            }
            sub_chunks.append(sub_chunk)
        
        return sub_chunks
    
    def _extract_headers(self, text: str) -> List[str]:
        """Extract potential headers from text."""
        headers = []
        
        # Look for lines that might be headers (short, capitalized, etc.)
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if (len(line) < 100 and 
                len(line.split()) <= 10 and 
                (line.isupper() or line.istitle())):
                headers.append(line)
        
        return headers[:3]  # Return max 3 headers
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract potential dates from text."""
        # Common date patterns
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # MM/DD/YYYY or DD/MM/YYYY
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',    # YYYY/MM/DD
            r'\w+\s+\d{1,2},?\s+\d{4}',         # Month DD, YYYY
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        return list(set(dates))[:5]  # Return max 5 unique dates
    
    def _extract_numbers(self, text: str) -> List[str]:
        """Extract potential numbers/amounts from text."""
        # Look for currency amounts and large numbers
        number_patterns = [
            r'[\$€£¥₹]\s*\d+(?:,\d{3})*(?:\.\d+)?',  # Currency amounts
            r'\d+(?:,\d{3})*(?:\.\d+)?',              # Numbers with commas
        ]
        
        numbers = []
        for pattern in number_patterns:
            matches = re.findall(pattern, text)
            numbers.extend(matches)
        
        return list(set(numbers))[:10]  # Return max 10 unique numbers
    
    def _extract_simple_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract simple entities using pattern matching."""
        entities = {
            'emails': [],
            'phones': [],
            'urls': [],
            'names': []
        }
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities['emails'] = re.findall(email_pattern, text)
        
        # Phone numbers
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
        entities['phones'] = re.findall(phone_pattern, text)
        
        # URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        entities['urls'] = re.findall(url_pattern, text)
        
        # Simple name patterns (capitalized words)
        name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        entities['names'] = re.findall(name_pattern, text)[:5]  # Limit to 5 names
        
        # Remove empty categories
        entities = {k: v for k, v in entities.items() if v}
        
        return entities
