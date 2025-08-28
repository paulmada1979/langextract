"""
LangExtract Custom Component for Langflow

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

from langflow import CustomComponent
from langflow.field_typing import Data


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
    original_text: str
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
            logging.info(f"Processing {len(documents)} documents with schemas: {schemas}")
            response = self.session.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logging.info(f"Successfully processed {len(documents)} documents")
            return result
            
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {e}")
            raise RuntimeError(f"Failed to communicate with LangExtract API: {e}")
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse API response: {e}")
            raise RuntimeError("Invalid response from LangExtract API")
    
    def health_check(self) -> bool:
        """Check if the API is healthy and accessible."""
        try:
            url = f"{self.base_url}/health/"
            response = self.session.get(url, timeout=10)
            return response.status_code == 200
        except:
            return False


class LangExtractComponent(CustomComponent):
    """
    Langflow component for LangExtract API integration.
    
    This component processes document chunks using the deployed LangExtract application
    and returns structured extraction results.
    """
    
    display_name = "LangExtract Processor"
    description = "Process document chunks using LangExtract API with configurable schemas"
    documentation = "https://langextract.ai-did-it.eu"
    
    def build_config(self):
        """Build the component configuration."""
        return {
            "api_url": {
                "display_name": "API URL",
                "type": "str",
                "default": "https://langextract.ai-did-it.eu",
                "required": True,
                "description": "Base URL of the LangExtract API"
            },
            "text_chunks": {
                "display_name": "Text Chunks",
                "type": "Data",
                "required": True,
                "description": "List of text chunks to process (from dockling chunker)"
            },
            "document_ids": {
                "display_name": "Document IDs",
                "type": "Data",
                "required": True,
                "description": "Corresponding document IDs for each chunk"
            },
            "chunk_ids": {
                "display_name": "Chunk IDs",
                "type": "Data",
                "required": True,
                "description": "Corresponding chunk IDs for each chunk"
            },
            "schemas": {
                "display_name": "Schemas",
                "type": "list",
                "required": True,
                "default": ["invoice"],
                "description": "Schemas to apply for processing",
                "options": [
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
            },
            "extract_entities": {
                "display_name": "Extract Entities",
                "type": "bool",
                "default": True,
                "description": "Whether to extract entities from text"
            },
            "extract_categories": {
                "display_name": "Extract Categories",
                "type": "bool",
                "default": True,
                "description": "Whether to extract categories from text"
            },
            "confidence_threshold": {
                "display_name": "Confidence Threshold",
                "type": "float",
                "default": 0.7,
                "min": 0.0,
                "max": 1.0,
                "description": "Minimum confidence threshold for extractions"
            },
            "timeout": {
                "display_name": "Timeout (seconds)",
                "type": "int",
                "default": 30,
                "min": 10,
                "max": 300,
                "description": "API request timeout in seconds"
            }
        }
    
    def build(
        self,
        api_url: str = "https://langextract.ai-did-it.eu",
        text_chunks: Data = None,
        document_ids: Data = None,
        chunk_ids: Data = None,
        schemas: List[str] = ["invoice"],
        extract_entities: bool = True,
        extract_categories: bool = True,
        confidence_threshold: float = 0.7,
        timeout: int = 30
    ) -> Data:
        """
        Process document chunks using the LangExtract API.
        
        Args:
            api_url: Base URL of the LangExtract API
            text_chunks: List of text chunks to process
            document_ids: Corresponding document IDs
            chunk_ids: Corresponding chunk IDs
            schemas: Schemas to apply for processing
            extract_entities: Whether to extract entities
            extract_categories: Whether to extract categories
            confidence_threshold: Confidence threshold for extractions
            timeout: API request timeout
            
        Returns:
            Processing results as structured data
        """
        
        # Validate inputs
        if not text_chunks or not document_ids or not chunk_ids:
            raise ValueError("Text chunks, document IDs, and chunk IDs are required")
        
        # Convert inputs to lists if they're not already
        if isinstance(text_chunks, (str, list)):
            text_chunks_list = text_chunks if isinstance(text_chunks, list) else [text_chunks]
        else:
            # Handle Data objects from Langflow
            text_chunks_list = self._extract_text_from_data(text_chunks)
        
        if isinstance(document_ids, (str, list)):
            document_ids_list = document_ids if isinstance(document_ids, list) else [document_ids]
        else:
            document_ids_list = self._extract_ids_from_data(document_ids)
        
        if isinstance(chunk_ids, (str, list)):
            chunk_ids_list = chunk_ids if isinstance(chunk_ids, list) else [chunk_ids]
        else:
            chunk_ids_list = self._extract_ids_from_data(chunk_ids)
        
        # Validate list lengths
        if len(text_chunks_list) != len(document_ids_list) or len(text_chunks_list) != len(chunk_ids_list):
            raise ValueError("All input lists must have the same length")
        
        # Create processing options
        options = ProcessingOptions(
            extract_entities=extract_entities,
            extract_categories=extract_categories,
            confidence_threshold=confidence_threshold
        )
        
        # Create client and process documents
        try:
            client = LangExtractClient(api_url, timeout)
            
            # Create document chunk objects
            documents = []
            for i, (text, doc_id, chunk_id) in enumerate(zip(text_chunks_list, document_ids_list, chunk_ids_list)):
                documents.append(DocumentChunk(
                    text=str(text),
                    document_id=str(doc_id),
                    chunk_id=str(chunk_id)
                ))
            
            # Process documents
            result = client.process_documents(documents, schemas, options)
            
            # Convert to ProcessingResult objects
            processed_results = []
            for doc_result in result.get('processed_documents', []):
                processed_results.append(ProcessingResult(
                    chunk_id=doc_result['chunk_id'],
                    document_id=doc_result['document_id'],
                    original_text=doc_result['original_text'],
                    extracted_data=doc_result['extracted_data'],
                    embeddings=doc_result['embeddings'],
                    metadata=doc_result['metadata'],
                    processing_time=doc_result['metadata']['processing_time'],
                    schemas_applied=doc_result['metadata']['schemas_applied']
                ))
            
            # Return results as Langflow Data
            return self._create_result_data(processed_results, result.get('summary', {}))
            
        except Exception as e:
            logging.error(f"Error processing documents: {e}")
            raise RuntimeError(f"Failed to process documents: {e}")
    
    def _extract_text_from_data(self, data: Data) -> List[str]:
        """Extract text content from Langflow Data object."""
        if hasattr(data, 'data') and isinstance(data.data, list):
            return [str(item.get('text', item)) if isinstance(item, dict) else str(item) for item in data.data]
        elif hasattr(data, 'data'):
            return [str(data.data)]
        else:
            return [str(data)]
    
    def _extract_ids_from_data(self, data: Data) -> List[str]:
        """Extract IDs from Langflow Data object."""
        if hasattr(data, 'data') and isinstance(data.data, list):
            return [str(item.get('id', item)) if isinstance(item, dict) else str(item) for item in data.data]
        elif hasattr(data, 'data'):
            return [str(data.data)]
        else:
            return [str(data)]
    
    def _create_result_data(self, results: List[ProcessingResult], summary: Dict[str, Any]) -> Data:
        """Create Langflow Data object from processing results."""
        result_data = []
        
        for result in results:
            result_data.append({
                "chunk_id": result.chunk_id,
                "document_id": result.document_id,
                "original_text": result.original_text,
                "extracted_data": result.extracted_data,
                "embeddings": result.embeddings,
                "metadata": result.metadata,
                "processing_time": result.processing_time,
                "schemas_applied": result.schemas_applied
            })
        
        # Create summary record
        summary_record = {
            "type": "summary",
            "total_chunks": summary.get('total_chunks', 0),
            "processed_chunks": summary.get('processed_chunks', 0),
            "failed_chunks": summary.get('failed_chunks', 0),
            "total_processing_time": summary.get('total_processing_time', 0.0)
        }
        
        # Return as Data object
        return Data(data=result_data, metadata={"summary": summary_record})


# Utility functions for standalone use
def create_langextract_component(api_url: str = "https://langextract.ai-did-it.eu") -> LangExtractClient:
    """Factory function to create a LangExtract client instance."""
    return LangExtractClient(api_url)


def process_dockling_chunks(
    text_chunks: List[str],
    document_ids: List[str],
    chunk_ids: List[str],
    schemas: List[str],
    api_url: str = "https://langextract.ai-did-it.eu",
    options: Optional[ProcessingOptions] = None
) -> List[ProcessingResult]:
    """Convenience function to process dockling chunks directly."""
    client = create_langextract_component(api_url)
    
    # Create document chunks
    documents = []
    for text, doc_id, chunk_id in zip(text_chunks, document_ids, chunk_ids):
        documents.append(DocumentChunk(
            text=text,
            document_id=doc_id,
            chunk_id=chunk_id
        ))
    
    # Process documents
    result = client.process_documents(documents, schemas, options)
    
    # Convert to ProcessingResult objects
    processed_results = []
    for doc_result in result.get('processed_documents', []):
        processed_results.append(ProcessingResult(
            chunk_id=doc_result['chunk_id'],
            document_id=doc_result['document_id'],
            original_text=doc_result['original_text'],
            extracted_data=doc_result['extracted_data'],
            embeddings=doc_result['embeddings'],
            metadata=doc_result['metadata'],
            processing_time=doc_result['metadata']['processing_time'],
            schemas_applied=doc_result['metadata']['schemas_applied']
        ))
    
    return processed_results


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
    print("LangExtract Langflow Component")
    print("=" * 40)
    
    # Create component
    component = LangExtractComponent()
    
    # Show available schemas
    print("\nAvailable schemas:")
    client = create_langextract_component()
    schema_info = client.get_available_schemas()
    for schema, description in schema_info['descriptions'].items():
        print(f"  - {schema}: {description}")
    
    # Show recommended combinations
    print("\nRecommended schema combinations:")
    for combo in get_recommended_schema_combinations():
        print(f"  - {', '.join(combo)}")
    
    print("\nComponent ready for use in Langflow!")

