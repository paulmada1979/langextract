"""
LangExtract Custom Component for Langflow

Copy and paste this entire code into Langflow's custom component editor.
This component processes document chunks using the LangExtract API.
"""

import json
import logging
from typing import Dict, List, Any, Optional
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
        """
        
        # Validate inputs
        if not text_chunks or not document_ids or not chunk_ids:
            raise ValueError("Text chunks, document IDs, and chunk IDs are required")
        
        # Extract data from Langflow Data objects
        text_chunks_list = self._extract_list_from_data(text_chunks)
        document_ids_list = self._extract_list_from_data(document_ids)
        chunk_ids_list = self._extract_list_from_data(chunk_ids)
        
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
            client = self._create_client(api_url, timeout)
            
            # Create document chunk objects
            documents = []
            for text, doc_id, chunk_id in zip(text_chunks_list, document_ids_list, chunk_ids_list):
                documents.append(DocumentChunk(
                    text=str(text),
                    document_id=str(doc_id),
                    chunk_id=str(chunk_id)
                ))
            
            # Process documents
            result = self._process_documents(client, documents, schemas, options)
            
            # Return results as Langflow Data
            return self._create_result_data(result)
            
        except Exception as e:
            logging.error(f"Error processing documents: {e}")
            raise RuntimeError(f"Failed to process documents: {e}")
    
    def _extract_list_from_data(self, data: Data) -> List[str]:
        """Extract list from Langflow Data object."""
        if hasattr(data, 'data'):
            if isinstance(data.data, list):
                return [str(item) for item in data.data]
            else:
                return [str(data.data)]
        else:
            return [str(data)]
    
    def _create_client(self, api_url: str, timeout: int):
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
        
        return {
            'session': session,
            'base_url': api_url.rstrip('/'),
            'timeout': timeout
        }
    
    def _process_documents(self, client, documents: List[DocumentChunk], schemas: List[str], options: ProcessingOptions) -> Dict[str, Any]:
        """Process documents using the LangExtract API."""
        
        # Validate schemas
        available_schemas = [
            "support_case", "refund_case", "invoice", "contract_terms",
            "sop_steps", "price_list", "product_spec", "faq", "policy"
        ]
        
        invalid_schemas = [s for s in schemas if s not in available_schemas]
        if invalid_schemas:
            raise ValueError(f"Invalid schemas: {invalid_schemas}. Available: {available_schemas}")
        
        # Prepare request payload
        payload = {
            "documents": [asdict(doc) for doc in documents],
            "schemas": schemas
        }
        
        if options:
            payload["options"] = asdict(options)
        
        # Make API request
        url = f"{client['base_url']}/api/process/"
        
        try:
            logging.info(f"Processing {len(documents)} documents with schemas: {schemas}")
            response = client['session'].post(
                url,
                json=payload,
                timeout=client['timeout']
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
    
    def _create_result_data(self, result: Dict[str, Any]) -> Data:
        """Create Langflow Data object from processing results."""
        result_data = []
        
        for doc_result in result.get('processed_documents', []):
            result_data.append({
                "chunk_id": doc_result.get('chunk_id', ''),
                "document_id": doc_result.get('document_id', ''),
                "content": doc_result.get('original_text', ''),
                "extracted_data": doc_result.get('extracted_data', {}),
                "embeddings": doc_result.get('embeddings', {}),
                "metadata": doc_result.get('metadata', {}),
                "processing_time": doc_result.get('metadata', {}).get('processing_time', 0.0),
                "schemas_applied": doc_result.get('metadata', {}).get('schemas_applied', [])
            })
        
        # Create summary record
        summary = result.get('summary', {})
        summary_record = {
            "type": "summary",
            "total_chunks": summary.get('total_chunks', 0),
            "processed_chunks": summary.get('processed_chunks', 0),
            "failed_chunks": summary.get('failed_chunks', 0),
            "total_processing_time": summary.get('total_processing_time', 0.0)
        }
        
        # Return as Data object
        return Data(data=result_data, metadata={"summary": summary_record})
