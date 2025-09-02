"""
Custom Component for LangExtract API Integration

This component provides a seamless interface to communicate with the deployed
LangExtract application at https://langextract.ai-did-it.eu/api/process/

Features:
- Direct integration with dockling chunker
- Support for all available schemas
- Configurable processing options
- Error handling and retry logic
- Batch processing capabilities
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a document chunk for processing."""
    text: str
    document_id: str
    chunk_id: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProcessingOptions:
    """Configuration options for document processing."""
    extract_entities: bool = True
    extract_categories: bool = True
    confidence_threshold: float = 0.7


@dataclass
class ProcessingResult:
    """Result of document processing."""
    chunk_id: str
    document_id: str
    content: str
    extracted_data: Dict[str, Any]
    embeddings: Dict[str, Any]
    metadata: Dict[str, Any]
    processing_time: float
    schemas_applied: List[str]


class LangExtractClient:
    """Client for communicating with the LangExtract API."""
    
    def __init__(self, base_url: str = "https://langextract.ai-did-it.eu", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = self._create_session()
        
        # Available schemas from the registry
        self.available_schemas = [
            "support_case",
            "refund_case", 
            "invoice",
            "contract_terms",
            "sop_steps",
            "price_list",
            "product_spec",
            "faq",
            "policy"
        ]
        
        # Schema descriptions for better UX
        self.schema_descriptions = {
            "support_case": "Support/inquiry email or ticket processing",
            "refund_case": "Refund case processing with retail domain support",
            "invoice": "Invoice document processing and data extraction",
            "contract_terms": "Contract terms and conditions extraction",
            "sop_steps": "Standard Operating Procedure steps extraction",
            "price_list": "Price list and pricing information extraction",
            "product_spec": "Product specification extraction with retail domain support",
            "faq": "Frequently Asked Questions processing",
            "policy": "Policy document processing and clause extraction"
        }
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def get_available_schemas(self) -> Dict[str, Any]:
        """Get list of available schemas and their descriptions."""
        return {
            "schemas": self.available_schemas,
            "descriptions": self.schema_descriptions
        }
    
    def process_documents(
        self,
        documents: List[DocumentChunk],
        schemas: List[str],
        options: Optional[ProcessingOptions] = None
    ) -> Dict[str, Any]:
        """
        Process documents using the LangExtract API.
        
        Args:
            documents: List of document chunks to process
            schemas: List of schema names to apply
            options: Processing options configuration
            
        Returns:
            API response with processing results
        """
        if not documents:
            raise ValueError("At least one document must be provided")
        
        if not schemas:
            raise ValueError("At least one schema must be specified")
        
        # Validate schemas
        invalid_schemas = [s for s in schemas if s not in self.available_schemas]
        if invalid_schemas:
            raise ValueError(f"Invalid schemas: {invalid_schemas}. Available: {self.available_schemas}")
        
        # Prepare request payload
        payload = {
            "documents": [asdict(doc) for doc in documents],
            "schemas": schemas
        }
        
        if options:
            payload["options"] = asdict(options)
        
        # Make API request
        url = f"{self.base_url}/api/process/"
        
        try:
            logger.info(f"Processing {len(documents)} documents with schemas: {schemas}")
            response = self.session.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully processed {len(documents)} documents")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise RuntimeError(f"Failed to communicate with LangExtract API: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response: {e}")
            raise RuntimeError("Invalid response from LangExtract API")
    
    def health_check(self) -> bool:
        """Check if the API is healthy and accessible."""
        try:
            url = f"{self.base_url}/health/"
            response = self.session.get(url, timeout=10)
            return response.status_code == 200
        except:
            return False


class LangExtractComponent:
    """
    Main component class that integrates with dockling chunker and provides
    a user-friendly interface for document processing.
    """
    
    def __init__(self, api_url: str = "https://langextract.ai-did-it.eu"):
        self.client = LangExtractClient(api_url)
        self.processing_history = []
        
    def get_schema_info(self) -> Dict[str, Any]:
        """Get comprehensive information about available schemas."""
        return self.client.get_available_schemas()
    
    def process_text_chunks(
        self,
        text_chunks: List[str],
        document_ids: List[str],
        chunk_ids: List[str],
        schemas: List[str],
        options: Optional[ProcessingOptions] = None,
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[ProcessingResult]:
        """
        Process text chunks directly from dockling chunker output.
        
        Args:
            text_chunks: List of text content from chunks
            document_ids: Corresponding document IDs
            chunk_ids: Corresponding chunk IDs
            schemas: Schemas to apply for processing
            options: Processing options
            metadata: Optional metadata for each chunk
            
        Returns:
            List of processing results
        """
        if len(text_chunks) != len(document_ids) or len(text_chunks) != len(chunk_ids):
            raise ValueError("All input lists must have the same length")
        
        # Create document chunk objects
        documents = []
        for i, (text, doc_id, chunk_id) in enumerate(zip(text_chunks, document_ids, chunk_ids)):
            chunk_metadata = metadata[i] if metadata and i < len(metadata) else None
            documents.append(DocumentChunk(
                text=text,
                document_id=doc_id,
                chunk_id=chunk_id,
                metadata=chunk_metadata
            ))
        
        # Process documents
        result = self.client.process_documents(documents, schemas, options)
        
        # Convert to ProcessingResult objects
        processed_results = []
        for doc_result in result.get('processed_documents', []):
            processed_results.append(ProcessingResult(
                chunk_id=doc_result['chunk_id'],
                document_id=doc_result['document_id'],
                content=doc_result['original_text'],
                extracted_data=doc_result['extracted_data'],
                embeddings=doc_result['embeddings'],
                metadata=doc_result['metadata'],
                processing_time=doc_result['metadata']['processing_time'],
                schemas_applied=doc_result['metadata']['schemas_applied']
            ))
        
        # Store in history
        self.processing_history.append({
            'timestamp': time.time(),
            'chunks_processed': len(processed_results),
            'schemas_used': schemas,
            'summary': result.get('summary', {})
        })
        
        return processed_results
    
    def process_single_chunk(
        self,
        text: str,
        document_id: str,
        chunk_id: str,
        schemas: List[str],
        options: Optional[ProcessingOptions] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProcessingResult:
        """
        Process a single text chunk.
        
        Args:
            text: Text content to process
            document_id: Document identifier
            chunk_id: Chunk identifier
            schemas: Schemas to apply
            options: Processing options
            metadata: Optional metadata
            
        Returns:
            Processing result for the chunk
        """
        results = self.process_text_chunks(
            [text], [document_id], [chunk_id], schemas, options, [metadata]
        )
        return results[0] if results else None
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get summary of all processing operations."""
        if not self.processing_history:
            return {"message": "No processing history available"}
        
        total_chunks = sum(h['chunks_processed'] for h in self.processing_history)
        total_operations = len(self.processing_history)
        
        # Get unique schemas used
        all_schemas = set()
        for h in self.processing_history:
            all_schemas.update(h['schemas_used'])
        
        return {
            "total_chunks_processed": total_chunks,
            "total_operations": total_operations,
            "unique_schemas_used": list(all_schemas),
            "recent_operations": self.processing_history[-5:] if len(self.processing_history) > 5 else self.processing_history
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to the LangExtract API."""
        try:
            is_healthy = self.client.health_check()
            schemas = self.client.get_available_schemas()
            
            return {
                "status": "success" if is_healthy else "warning",
                "api_accessible": is_healthy,
                "available_schemas": len(schemas["schemas"]),
                "message": "API is accessible and ready" if is_healthy else "API health check failed"
            }
        except Exception as e:
            return {
                "status": "error",
                "api_accessible": False,
                "error": str(e),
                "message": "Failed to connect to API"
            }


# Example usage and integration functions
def create_langextract_component(api_url: str = "https://langextract.ai-did-it.eu") -> LangExtractComponent:
    """
    Factory function to create a LangExtract component instance.
    
    Args:
        api_url: Base URL of the deployed LangExtract application
        
    Returns:
        Configured LangExtractComponent instance
    """
    return LangExtractComponent(api_url)


def process_dockling_chunks(
    text_chunks: List[str],
    document_ids: List[str],
    chunk_ids: List[str],
    schemas: List[str],
    api_url: str = "https://langextract.ai-did-it.eu",
    options: Optional[ProcessingOptions] = None
) -> List[ProcessingResult]:
    """
    Convenience function to process dockling chunks directly.
    
    Args:
        text_chunks: List of text content from dockling chunker
        document_ids: Corresponding document IDs
        chunk_ids: Corresponding chunk IDs
        schemas: Schemas to apply for processing
        api_url: LangExtract API URL
        options: Processing options
        
    Returns:
        List of processing results
    """
    component = create_langextract_component(api_url)
    return component.process_text_chunks(
        text_chunks, document_ids, chunk_ids, schemas, options
    )


# Configuration and utility functions
def get_default_processing_options() -> ProcessingOptions:
    """Get default processing options."""
    return ProcessingOptions(
        extract_entities=True,
        extract_categories=True,
        confidence_threshold=0.7
    )


def get_recommended_schema_combinations() -> List[List[str]]:
    """Get recommended schema combinations for different use cases."""
    return [
        ["invoice"],  # Invoice processing
        ["support_case"],  # Support ticket processing
        ["refund_case"],  # Refund processing
        ["product_spec"],  # Product specification
        ["contract_terms"],  # Contract analysis
        ["policy"],  # Policy document processing
        ["invoice", "support_case"],  # Invoice + support combination
        ["refund_case", "support_case"],  # Refund + support combination
        ["product_spec", "price_list"],  # Product + pricing combination
    ]


if __name__ == "__main__":
    # Example usage and testing
    print("LangExtract Custom Component")
    print("=" * 40)
    
    # Create component
    component = create_langextract_component()
    
    # Test connection
    print("\nTesting API connection...")
    connection_status = component.test_connection()
    print(f"Status: {connection_status['status']}")
    print(f"API Accessible: {connection_status['api_accessible']}")
    
    # Show available schemas
    print("\nAvailable schemas:")
    schema_info = component.get_schema_info()
    for schema, description in schema_info['descriptions'].items():
        print(f"  - {schema}: {description}")
    
    # Show recommended combinations
    print("\nRecommended schema combinations:")
    for combo in get_recommended_schema_combinations():
        print(f"  - {', '.join(combo)}")
    
    print("\nComponent ready for use!")
