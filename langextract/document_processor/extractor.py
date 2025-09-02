"""
Metadata extractor that integrates with langextract for structured data extraction.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from core.schema_extractor import schema_extractor
from core.openai_client import openai_client

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    Metadata extractor that uses langextract schemas to extract structured data
    from document chunks.
    """
    
    def __init__(self):
        """Initialize the metadata extractor."""
        self.default_schemas = ['invoice', 'support_case', 'refund_case']
        logger.info("MetadataExtractor initialized")
    
    async def extract_metadata(self, text: str, schemas: List[str] = None) -> Dict[str, Any]:
        """
        Extract metadata from text using langextract schemas.
        
        Args:
            text: Text content to process
            schemas: List of schemas to apply
            
        Returns:
            Dictionary containing extracted metadata
        """
        if not text or not text.strip():
            return {}
        
        schemas = schemas or self.default_schemas
        
        try:
            # Run schema extraction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._run_schema_extraction, text, schemas
            )
            
            # Enhance with additional metadata
            enhanced_result = await self._enhance_metadata(result, text)
            
            logger.debug(f"Extracted metadata for text of length {len(text)}")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
            return {'error': str(e)}
    
    def _run_schema_extraction(self, text: str, schemas: List[str]) -> Dict[str, Any]:
        """Run schema extraction (synchronous)."""
        try:
            # Prepare options for schema extraction
            options = {
                'extract_entities': True,
                'extract_categories': True,
                'confidence_threshold': 0.7
            }
            
            # Extract using langextract
            result = schema_extractor.extract_from_chunk(text, schemas, options)
            
            return result
            
        except Exception as e:
            logger.error(f"Schema extraction failed: {e}")
            return {'error': str(e)}
    
    async def _enhance_metadata(self, base_result: Dict[str, Any], text: str) -> Dict[str, Any]:
        """Enhance metadata with additional information."""
        enhanced = {
            'langextract_result': base_result,
            'text_analysis': {},
            'content_insights': {}
        }
        
        try:
            # Analyze text characteristics
            enhanced['text_analysis'] = await self._analyze_text_characteristics(text)
            
            # Extract content insights
            enhanced['content_insights'] = await self._extract_content_insights(text, base_result)
            
            # Add processing metadata
            enhanced['processing_metadata'] = {
                'text_length': len(text),
                'word_count': len(text.split()),
                'sentence_count': len([s for s in text.split('.') if s.strip()]),
                'extraction_timestamp': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.warning(f"Failed to enhance metadata: {e}")
            enhanced['enhancement_error'] = str(e)
        
        return enhanced
    
    async def _analyze_text_characteristics(self, text: str) -> Dict[str, Any]:
        """Analyze basic text characteristics."""
        analysis = {
            'language_indicators': {},
            'document_type_indicators': {},
            'content_density': {}
        }
        
        try:
            # Language indicators
            analysis['language_indicators'] = self._detect_language_indicators(text)
            
            # Document type indicators
            analysis['document_type_indicators'] = self._detect_document_type(text)
            
            # Content density analysis
            analysis['content_density'] = self._analyze_content_density(text)
            
        except Exception as e:
            logger.warning(f"Failed to analyze text characteristics: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    async def _extract_content_insights(self, text: str, langextract_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract additional content insights."""
        insights = {
            'key_topics': [],
            'important_entities': [],
            'document_sections': [],
            'action_items': []
        }
        
        try:
            # Extract key topics
            insights['key_topics'] = self._extract_key_topics(text)
            
            # Extract important entities
            insights['important_entities'] = self._extract_important_entities(text, langextract_result)
            
            # Identify document sections
            insights['document_sections'] = self._identify_document_sections(text)
            
            # Extract potential action items
            insights['action_items'] = self._extract_action_items(text)
            
        except Exception as e:
            logger.warning(f"Failed to extract content insights: {e}")
            insights['error'] = str(e)
        
        return insights
    
    def _detect_language_indicators(self, text: str) -> Dict[str, Any]:
        """Detect language indicators from text."""
        indicators = {
            'primary_language': 'en',  # Default to English
            'confidence': 0.5,
            'indicators': []
        }
        
        # Simple language detection based on common words
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        spanish_words = ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le']
        french_words = ['le', 'la', 'de', 'et', 'à', 'un', 'il', 'que', 'ne', 'se', 'ce', 'pas']
        
        text_lower = text.lower()
        
        english_count = sum(1 for word in english_words if word in text_lower)
        spanish_count = sum(1 for word in spanish_words if word in text_lower)
        french_count = sum(1 for word in french_words if word in text_lower)
        
        if english_count > spanish_count and english_count > french_count:
            indicators['primary_language'] = 'en'
            indicators['confidence'] = min(0.9, english_count / 10)
        elif spanish_count > french_count:
            indicators['primary_language'] = 'es'
            indicators['confidence'] = min(0.9, spanish_count / 10)
        elif french_count > 0:
            indicators['primary_language'] = 'fr'
            indicators['confidence'] = min(0.9, french_count / 10)
        
        return indicators
    
    def _detect_document_type(self, text: str) -> Dict[str, Any]:
        """Detect document type based on content."""
        indicators = {
            'likely_types': [],
            'confidence_scores': {}
        }
        
        text_lower = text.lower()
        
        # Invoice indicators
        invoice_keywords = ['invoice', 'bill', 'payment', 'amount', 'total', 'due date', 'invoice number']
        invoice_score = sum(1 for keyword in invoice_keywords if keyword in text_lower)
        
        # Contract indicators
        contract_keywords = ['agreement', 'contract', 'terms', 'conditions', 'parties', 'signature', 'effective date']
        contract_score = sum(1 for keyword in contract_keywords if keyword in text_lower)
        
        # Support case indicators
        support_keywords = ['support', 'ticket', 'issue', 'problem', 'help', 'assistance', 'complaint']
        support_score = sum(1 for keyword in support_keywords if keyword in text_lower)
        
        # Refund indicators
        refund_keywords = ['refund', 'return', 'cancel', 'reimbursement', 'money back']
        refund_score = sum(1 for keyword in refund_keywords if keyword in text_lower)
        
        # Calculate scores
        scores = {
            'invoice': invoice_score / len(invoice_keywords),
            'contract': contract_score / len(contract_keywords),
            'support_case': support_score / len(support_keywords),
            'refund_case': refund_score / len(refund_keywords)
        }
        
        # Sort by score
        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        indicators['likely_types'] = [doc_type for doc_type, score in sorted_types if score > 0.1]
        indicators['confidence_scores'] = scores
        
        return indicators
    
    def _analyze_content_density(self, text: str) -> Dict[str, Any]:
        """Analyze content density and structure."""
        density = {
            'information_density': 0.0,
            'structure_score': 0.0,
            'readability_indicators': {}
        }
        
        try:
            # Calculate information density (non-whitespace characters / total characters)
            non_whitespace = len([c for c in text if not c.isspace()])
            density['information_density'] = non_whitespace / len(text) if text else 0
            
            # Calculate structure score based on formatting
            lines = text.split('\n')
            structured_lines = sum(1 for line in lines if line.strip() and (line.startswith(('•', '-', '*', '1.', '2.', '3.')) or ':' in line))
            density['structure_score'] = structured_lines / len(lines) if lines else 0
            
            # Readability indicators
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
            
            density['readability_indicators'] = {
                'average_sentence_length': avg_sentence_length,
                'sentence_count': len(sentences),
                'paragraph_count': len([p for p in text.split('\n\n') if p.strip()])
            }
            
        except Exception as e:
            logger.warning(f"Failed to analyze content density: {e}")
            density['error'] = str(e)
        
        return density
    
    def _extract_key_topics(self, text: str) -> List[str]:
        """Extract key topics from text."""
        topics = []
        
        # Simple topic extraction based on repeated important words
        words = text.lower().split()
        
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
        
        # Count word frequency
        word_freq = {}
        for word in words:
            word = word.strip('.,!?;:"()[]{}')
            if len(word) > 3 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get most frequent words as topics
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        topics = [word for word, freq in sorted_words[:10] if freq > 1]
        
        return topics
    
    def _extract_important_entities(self, text: str, langextract_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract important entities from text and langextract results."""
        entities = []
        
        try:
            # Get entities from langextract result
            langextract_data = langextract_result.get('extracted_data', {})
            langextract_entities = langextract_data.get('entities', [])
            
            for entity in langextract_entities:
                entities.append({
                    'text': entity.get('text', ''),
                    'label': entity.get('label', ''),
                    'confidence': entity.get('confidence', 0.0),
                    'source': 'langextract'
                })
            
            # Add simple pattern-based entities
            import re
            
            # Email addresses
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            for email in emails[:3]:  # Limit to 3 emails
                entities.append({
                    'text': email,
                    'label': 'EMAIL',
                    'confidence': 0.9,
                    'source': 'pattern'
                })
            
            # Phone numbers
            phones = re.findall(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b', text)
            for phone in phones[:3]:  # Limit to 3 phones
                entities.append({
                    'text': phone,
                    'label': 'PHONE',
                    'confidence': 0.8,
                    'source': 'pattern'
                })
            
            # Currency amounts
            amounts = re.findall(r'[\$€£¥₹]\s*\d+(?:,\d{3})*(?:\.\d+)?', text)
            for amount in amounts[:5]:  # Limit to 5 amounts
                entities.append({
                    'text': amount,
                    'label': 'MONEY',
                    'confidence': 0.9,
                    'source': 'pattern'
                })
            
        except Exception as e:
            logger.warning(f"Failed to extract important entities: {e}")
        
        return entities
    
    def _identify_document_sections(self, text: str) -> List[Dict[str, Any]]:
        """Identify document sections."""
        sections = []
        
        try:
            lines = text.split('\n')
            current_section = None
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Check if line looks like a header
                if (len(line) < 100 and 
                    len(line.split()) <= 10 and 
                    (line.isupper() or line.istitle()) and
                    not line.endswith('.') and
                    not line.endswith(',')):
                    
                    if current_section:
                        sections.append(current_section)
                    
                    current_section = {
                        'title': line,
                        'start_line': i,
                        'end_line': i,
                        'content_preview': ''
                    }
                elif current_section:
                    current_section['end_line'] = i
                    if not current_section['content_preview'] and len(line) > 20:
                        current_section['content_preview'] = line[:100] + '...' if len(line) > 100 else line
            
            # Add final section
            if current_section:
                sections.append(current_section)
            
        except Exception as e:
            logger.warning(f"Failed to identify document sections: {e}")
        
        return sections[:10]  # Limit to 10 sections
    
    def _extract_action_items(self, text: str) -> List[Dict[str, Any]]:
        """Extract potential action items from text."""
        action_items = []
        
        try:
            # Look for action-oriented phrases
            action_patterns = [
                r'(?:please|kindly|should|must|need to|required to)\s+([^.!?]+[.!?])',
                r'(?:action|task|todo|follow.?up|next step)[:\s]+([^.!?]+[.!?])',
                r'(?:deadline|due date|by)\s+([^.!?]+[.!?])',
            ]
            
            import re
            for pattern in action_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches[:3]:  # Limit to 3 per pattern
                    action_items.append({
                        'text': match.strip(),
                        'type': 'action_item',
                        'confidence': 0.7
                    })
            
        except Exception as e:
            logger.warning(f"Failed to extract action items: {e}")
        
        return action_items[:10]  # Limit to 10 action items
