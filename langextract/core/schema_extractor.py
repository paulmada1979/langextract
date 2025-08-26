"""
Schema extractor module for applying schemas to text chunks and extracting structured data.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from .schema_loader import schema_loader
from .openai_client import openai_client
import time

logger = logging.getLogger(__name__)


class SchemaExtractor:
    """Extracts structured data from text chunks based on defined schemas."""
    
    def __init__(self):
        self.schema_loader = schema_loader
        self.openai_client = openai_client
    
    def extract_from_chunk(self, text: str, schema_names: List[str], 
                          options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from a text chunk using specified schemas.
        
        Args:
            text: Text chunk to process
            schema_names: List of schema names to apply
            options: Processing options
            
        Returns:
            Dictionary containing extracted data and metadata
        """
        start_time = time.time()
        
        extracted_data = {
            'entities': [],
            'categories': [],
            'key_phrases': [],
            'schema_matches': {}
        }
        
        # Apply each schema
        for schema_name in schema_names:
            schema = self.schema_loader.get_schema(schema_name)
            if schema:
                logger.debug(f"Applying schema {schema_name} to text (length: {len(text)})")
                schema_data = self._apply_schema(text, schema, options)
                if schema_data:
                    extracted_data['schema_matches'][schema_name] = schema_data
                    logger.debug(f"Successfully extracted data for schema {schema_name}: {len(schema_data)} fields")
                else:
                    logger.debug(f"No data extracted for schema {schema_name}")
            else:
                logger.warning(f"Schema {schema_name} not found")
        
        # Extract entities if requested
        if options.get('extract_entities', False):
            extracted_data['entities'] = self._extract_entities(text)
        
        # Extract categories if requested
        if options.get('extract_categories', False):
            extracted_data['categories'] = self._extract_categories(text, extracted_data['schema_matches'])
        
        # Extract key phrases
        extracted_data['key_phrases'] = self._extract_key_phrases(text)
        
        processing_time = time.time() - start_time
        
        return {
            'extracted_data': extracted_data,
            'metadata': {
                'processing_time': round(processing_time, 3),
                'schemas_applied': schema_names
            }
        }
    
    def _apply_schema(self, text: str, schema: Dict[str, Any], 
                      options: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Apply a single schema to extract structured data.
        
        Args:
            text: Text to process
            schema: Schema definition
            options: Processing options
            
        Returns:
            Extracted data according to schema
        """
        if not schema or 'fields' not in schema:
            return None
        
        extracted_fields = {}
        confidence_threshold = options.get('confidence_threshold', 0.7)
        
        for field_name, field_def in schema['fields'].items():
            field_value = self._extract_field(text, field_name, field_def, schema)
            if field_value and field_value.get('confidence', 0) >= confidence_threshold:
                extracted_fields[field_name] = field_value['value']
                logger.debug(f"Extracted field {field_name}: {field_value['value']} (confidence: {field_value['confidence']})")
            else:
                logger.debug(f"Field {field_name} extraction failed or below threshold (confidence: {field_value.get('confidence', 0) if field_value else 'None'})")
        
        # Check required fields
        required_fields = schema.get('required', [])
        if required_fields and not all(field in extracted_fields for field in required_fields):
            logger.warning(f"Missing required fields for schema {schema.get('$id', 'unknown')}")
            return None
        
        return extracted_fields
    
    def _extract_field(self, text: str, field_name: str, field_def: Dict[str, Any], 
                       schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract a single field from text based on field definition.
        
        Args:
            text: Text to process
            field_name: Name of the field to extract
            field_def: Field definition from schema
            schema: Full schema definition
            
        Returns:
            Dictionary with 'value' and 'confidence' keys
        """
        field_type = field_def.get('type', 'string')
        
        if field_type == 'string':
            return self._extract_string_field(text, field_name, field_def, schema)
        elif field_type == 'list':
            return self._extract_list_field(text, field_name, field_def, schema)
        elif field_type == 'number':
            return self._extract_number_field(text, field_name, field_def, schema)
        elif field_type == 'object':
            return self._extract_object_field(text, field_name, field_def, schema)
        
        return None
    
    def _extract_string_field(self, text: str, field_name: str, field_def: Dict[str, Any], 
                              schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract a string field from text."""
        # Check if this is a span field
        if 'spans' in schema and field_name in schema['spans']:
            return self._extract_span_field(text, field_name, field_def)
        
        # Check for enum values
        if 'enum' in field_def:
            return self._extract_enum_field(text, field_name, field_def)
        
        # Check for enum references
        if 'enum_ref' in field_def:
            return self._extract_enum_ref_field(text, field_name, field_def)
        
        # Use pattern matching for common field types
        if field_name in ['effective_date', 'issue_date', 'due_date']:
            return self._extract_date_field(text, field_name)
        elif field_name in ['invoice_no', 'reference', 'invoice_number']:
            return self._extract_reference_field(text, field_name)
        elif field_name == 'currency':
            return self._extract_currency_field(text)
        elif field_name == 'customer':
            return self._extract_customer_field(text)
        elif field_name == 'status':
            return self._extract_status_field(text, field_def)
        
        # Default: extract text around field name
        return self._extract_named_field(text, field_name)
    
    def _extract_span_field(self, text: str, field_name: str, field_def: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text span for fields marked as spans."""
        # Simple pattern matching for spans
        patterns = {
            'payment_terms': r'payment\s+terms?[:\s]+([^.\n]+)',
            'termination_clause': r'termination[:\s]+([^.\n]+)',
            'governing_law': r'governing\s+law[:\s]+([^.\n]+)',
        }
        
        pattern = patterns.get(field_name, field_name.replace("_", r"\s+") + r"[:\s]+([^.\n]+)")
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            value = match.group(1).strip()
            return {'value': value, 'confidence': 0.8}
        
        return {'value': '', 'confidence': 0.0}
    
    def _extract_enum_field(self, text: str, field_name: str, field_def: Dict[str, Any]) -> Dict[str, Any]:
        """Extract enum field with predefined values."""
        enum_values = field_def['enum']
        text_lower = text.lower()
        
        for enum_value in enum_values:
            if enum_value.lower() in text_lower:
                return {'value': enum_value, 'confidence': 0.9}
        
        return {'value': '', 'confidence': 0.0}
    
    def _extract_enum_ref_field(self, text: str, field_name: str, field_def: Dict[str, Any]) -> Dict[str, Any]:
        """Extract enum field with vocabulary reference."""
        vocab_name, enum_name = field_def['enum_ref'].split('.')
        vocab = self.schema_loader.get_vocabulary(vocab_name)
        
        if not vocab or enum_name not in vocab:
            return {'value': '', 'confidence': 0.0}
        
        enum_values = vocab[enum_name]
        text_lower = text.lower()
        
        for enum_value in enum_values:
            if enum_value.lower() in text_lower:
                return {'value': enum_value, 'confidence': 0.9}
        
        return {'value': '', 'confidence': 0.0}
    
    def _extract_date_field(self, text: str, field_name: str) -> Dict[str, Any]:
        """Extract date fields using regex patterns."""
        # Common date patterns
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # MM/DD/YYYY or DD/MM/YYYY
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',    # YYYY/MM/DD
            r'\w+\s+\d{1,2},?\s+\d{4}',         # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return {'value': match.group(), 'confidence': 0.8}
        
        return {'value': '', 'confidence': 0.0}
    
    def _extract_reference_field(self, text: str, field_name: str) -> Dict[str, Any]:
        """Extract reference/invoice numbers."""
        # Look for patterns like "Invoice #12345" or "Ref: ABC-123"
        pattern = field_name.replace("_", r"\s+") + r"[:\s#]*([A-Z0-9\-]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            return {'value': match.group(1), 'confidence': 0.8}
        
        return {'value': '', 'confidence': 0.0}
    
    def _extract_currency_field(self, text: str) -> Dict[str, Any]:
        """Extract currency information."""
        # Look for currency symbols or codes
        currency_patterns = [
            r'[\$€£¥₹]',  # Currency symbols
            r'\b(USD|EUR|GBP|NGN|CNY)\b',  # Currency codes
        ]
        
        for pattern in currency_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {'value': match.group(), 'confidence': 0.9}
        
        return {'value': '', 'confidence': 0.0}
    
    def _extract_customer_field(self, text: str) -> Dict[str, Any]:
        """Extract customer information."""
        # Look for customer patterns
        customer_patterns = [
            r'customer[:\s]+([^.\n]+)',
            r'bill\s+to[:\s]+([^.\n]+)',
            r'sold\s+to[:\s]+([^.\n]+)',
            r'client[:\s]+([^.\n]+)',
        ]
        
        for pattern in customer_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                return {'value': value, 'confidence': 0.8}
        
        return {'value': '', 'confidence': 0.0}
    
    def _extract_status_field(self, text: str, field_def: Dict[str, Any]) -> Dict[str, Any]:
        """Extract status field with enum validation."""
        if 'enum' in field_def:
            enum_values = field_def['enum']
            text_lower = text.lower()
            
            for enum_value in enum_values:
                if enum_value.lower() in text_lower:
                    return {'value': enum_value, 'confidence': 0.9}
        
        return {'value': '', 'confidence': 0.0}
    
    def _extract_named_field(self, text: str, field_name: str) -> Dict[str, Any]:
        """Extract field by looking for field name in text."""
        # Look for patterns like "Field Name: value"
        pattern = field_name.replace("_", r"\s+") + r"[:\s]+([^.\n]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            value = match.group(1).strip()
            return {'value': value, 'confidence': 0.7}
        
        return {'value': '', 'confidence': 0.0}
    
    def _extract_list_field(self, text: str, field_name: str, field_def: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract list field."""
        if field_name == 'parties':
            # Extract parties from contract text
            parties = self._extract_parties(text)
            if parties:
                return {'value': parties, 'confidence': 0.8}
        
        # For other list fields, return empty list - can be enhanced with AI extraction
        return {'value': [], 'confidence': 0.5}
    
    def _extract_number_field(self, text: str, field_name: str, field_def: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract number field."""
        # Look for numbers in text, with context for specific field types
        if field_name in ['grand_total', 'total', 'amount']:
            # Look for total amounts with currency context
            pattern = r'(?:total|amount|sum|grand total)[:\s]*[\$€£¥₹]?\s*(\d+(?:,\d{3})*(?:\.\d+)?)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1).replace(',', ''))
                return {'value': value, 'confidence': 0.9}
        
        elif field_name in ['subtotal', 'tax_total']:
            # Look for subtotal or tax amounts
            pattern = field_name.replace("_", r"\s+") + r"[:\s]*[\$€£¥₹]?\s*(\d+(?:,\d{3})*(?:\.\d+)?)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1).replace(',', ''))
                return {'value': value, 'confidence': 0.8}
        
        # General number extraction
        pattern = r'\b\d+(?:,\d{3})*(?:\.\d+)?\b'
        matches = re.findall(pattern, text)
        
        if matches:
            # Convert to float, removing commas
            value = float(matches[0].replace(',', ''))
            return {'value': value, 'confidence': 0.7}
        
        return {'value': 0, 'confidence': 0.0}
    
    def _extract_object_field(self, text: str, field_name: str, field_def: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract object field."""
        # For now, return empty dict - can be enhanced with AI extraction
        return {'value': {}, 'confidence': 0.5}
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text."""
        # Simple entity extraction - can be enhanced with spaCy or OpenAI
        entities = []
        
        # Extract names (simple pattern)
        name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        names = re.findall(name_pattern, text)
        for name in names[:3]:  # Limit to 3 names
            entities.append({
                'text': name,
                'label': 'PERSON',
                'confidence': 0.8
            })
        
        # Extract money amounts
        money_pattern = r'[\$€£¥₹]\s*\d+(?:,\d{3})*(?:\.\d+)?'
        money_amounts = re.findall(money_pattern, text)
        for amount in money_amounts[:3]:  # Limit to 3 amounts
            entities.append({
                'text': amount,
                'label': 'MONEY',
                'confidence': 0.9
            })
        
        return entities
    
    def _extract_categories(self, text: str, schema_matches: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract categories based on schema matches."""
        categories = []
        
        # Determine categories based on schemas applied
        if 'contract_terms' in schema_matches:
            categories.append({
                'name': 'legal_contract',
                'confidence': 0.9
            })
        
        if 'invoice' in schema_matches:
            categories.append({
                'name': 'financial_document',
                'confidence': 0.9
            })
        
        if 'refund_case' in schema_matches:
            categories.append({
                'name': 'customer_service',
                'confidence': 0.8
            })
        
        return categories
    
    def _extract_parties(self, text: str) -> List[str]:
        """Extract parties from contract text."""
        parties = []
        
        # Look for party patterns
        party_patterns = [
            r'between\s+([^,]+?)\s+and\s+([^,]+?)(?:\s|$)',
            r'parties:\s*([^.\n]+)',
            r'(\w+(?:\s+\w+)*)\s+and\s+(\w+(?:\s+\w+)*)\s+agree',
            r'(\w+(?:\s+\w+)*)\s+,\s+(\w+(?:\s+\w+)*)\s+hereby',
        ]
        
        for pattern in party_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    parties.extend([party.strip() for party in match if party.strip()])
                else:
                    parties.append(match.strip())
        
        # Clean up parties (remove common words, duplicates)
        cleaned_parties = []
        for party in parties:
            party = party.strip()
            if party and len(party) > 2 and party.lower() not in ['and', 'the', 'of', 'in', 'to']:
                cleaned_parties.append(party)
        
        return list(set(cleaned_parties))[:5]  # Limit to 5 unique parties
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text."""
        # Simple key phrase extraction - can be enhanced with AI
        key_phrases = []
        
        # Look for important phrases (simplified)
        important_patterns = [
            r'\b(?:payment terms|termination clause|governing law)\b',
            r'\b(?:effective date|due date|issue date)\b',
            r'\b(?:parties|signatures|renewal)\b',
        ]
        
        for pattern in important_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            key_phrases.extend(matches)
        
        return list(set(key_phrases))[:5]  # Limit to 5 unique phrases


# Global schema extractor instance
schema_extractor = SchemaExtractor()
