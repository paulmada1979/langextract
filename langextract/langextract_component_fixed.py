"""
LangExtract Custom Component for Langflow - Dokling Integration (FIXED VERSION)

This component is specifically designed to work with Dokling chunker output
and process document chunks using the LangExtract API.

Copy and paste this entire code into Langflow's custom component editor.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from langflow.custom import Component
from langflow.io import DropdownInput, HandleInput, BoolInput, FloatInput, IntInput, StrInput, Output
from langflow.schema import Data, DataFrame


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


class LangExtractComponent(Component):
    """
    Langflow component for LangExtract API integration with Dokling chunker.
    
    This component processes Dokling document chunks using the deployed LangExtract application
    and returns the raw API response for pipeline integration.
    """
    
    display_name: str = "LangExtract Processor"
    description: str = "Process Dokling document chunks using LangExtract API with configurable schemas"
    documentation: str = "https://langextract.ai-did-it.eu"
    icon: str = "LangExtract"
    name: str = "LangExtractProcessor"

    inputs = [
        HandleInput(
            name="dokling_chunks",
            display_name="Dokling Chunks",
            info="Document chunks from Dokling chunker (DoclingDocument)",
            input_types=["Data", "DataFrame"],
            required=True,
        ),
        StrInput(
            name="api_url",
            display_name="API URL",
            info="Base URL of the LangExtract API",
            value="https://langextract.ai-did-it.eu",
            required=True,
        ),
        DropdownInput(
            name="schemas",
            display_name="Schemas",
            options=[
                "support_case",
                "refund_case", 
                "invoice",
                "contract_terms",
                "sop_steps",
                "price_list",
                "product_spec",
                "faq",
                "policy"
            ],
            info="Schemas to apply for processing (you can select multiple by separating with commas)",
            value="invoice",
            required=True,
        ),
        BoolInput(
            name="extract_entities",
            display_name="Extract Entities",
            info="Whether to extract entities from text",
            value=True,
            required=False,
        ),
        BoolInput(
            name="extract_categories",
            display_name="Extract Categories",
            info="Whether to extract categories from text",
            value=True,
            required=False,
        ),
        FloatInput(
            name="confidence_threshold",
            display_name="Confidence Threshold",
            info="Minimum confidence threshold for extractions (0.0 to 1.0)",
            value=0.7,
            required=False,
        ),
        IntInput(
            name="timeout",
            display_name="Timeout (seconds)",
            info="API request timeout in seconds (10 to 300)",
            value=30,
            required=False,
        ),
    ]

    outputs = [
        Output(display_name="API Response", name="api_response", method="process_chunks"),
    ]

    def process_chunks(self) -> Data:
        """
        Process Dokling document chunks using the LangExtract API.
        
        Returns:
            Raw LangExtract API response for pipeline integration
        """
        
        # Validate inputs
        if not self.dokling_chunks:
            raise ValueError("Dokling chunks are required")
        
        # Parse schemas (handle comma-separated values)
        schemas_list = self._parse_schemas(self.schemas)
        
        # Extract Dokling chunks and convert to LangExtract format
        documents = self._extract_dokling_chunks(self.dokling_chunks)
        
        if not documents:
            raise ValueError("No valid chunks found in Dokling output")
        
        # Log the number of documents being processed
        logging.info(f"Processing {len(documents)} documents with LangExtract API")
        
        # Validate confidence threshold
        if self.confidence_threshold < 0.0 or self.confidence_threshold > 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
        
        # Validate timeout
        if self.timeout < 10 or self.timeout > 300:
            raise ValueError("Timeout must be between 10 and 300 seconds")
        
        # Create processing options
        options = ProcessingOptions(
            extract_entities=self.extract_entities,
            extract_categories=self.extract_categories,
            confidence_threshold=self.confidence_threshold
        )
        
        # Create client and process documents
        try:
            client = self._create_client(self.api_url, self.timeout)
            
            # Process documents
            result = self._process_documents(client, documents, schemas_list, options)
            
            # Return the raw API response for pipeline integration
            return Data(data=result)
            
        except Exception as e:
            logging.error(f"Error processing documents: {e}")
            raise RuntimeError(f"Failed to process documents: {e}")
    
    def _parse_schemas(self, schemas_input: str) -> List[str]:
        """Parse schemas input, handling comma-separated values."""
        if isinstance(schemas_input, str):
            # Split by comma and clean up
            schemas = [s.strip() for s in schemas_input.split(',') if s.strip()]
        elif isinstance(schemas_input, list):
            schemas = schemas_input
        else:
            schemas = [str(schemas_input)]
        
        # Validate schemas
        available_schemas = [
            "support_case", "refund_case", "invoice", "contract_terms",
            "sop_steps", "price_list", "product_spec", "faq", "policy"
        ]
        
        valid_schemas = [s for s in schemas if s in available_schemas]
        if not valid_schemas:
            raise ValueError(f"No valid schemas found. Available: {available_schemas}")
        
        return valid_schemas
    
    def _extract_dokling_chunks(self, dokling_data) -> List[DocumentChunk]:
        """
        Extract and convert Dokling chunks to LangExtract format.
        
        FIXED: Now properly handles multiple chunks from the same document
        """
        documents = []
        
        try:
            # Handle different possible Dokling data structures
            chunks_data = self._extract_chunks_from_dokling_output(dokling_data)
            
            if not chunks_data:
                raise ValueError("No chunks found in Dokling output")
            
            logging.info(f"Found {len(chunks_data)} chunks in Dokling output")
            
            # Group chunks by document (if they have document_id)
            document_chunks = {}
            orphan_chunks = []
            
            for i, chunk in enumerate(chunks_data):
                # Extract text content from chunk
                text = self._extract_text_from_chunk(chunk)
                
                if text and text.strip():
                    # Try to extract document_id from chunk metadata
                    document_id = self._extract_document_id_from_chunk(chunk, i)
                    chunk_id = self._extract_chunk_id_from_chunk(chunk, i)
                    
                    # Extract metadata
                    metadata = self._extract_metadata_from_chunk(chunk)
                    
                    chunk_data = {
                        'text': text.strip(),
                        'document_id': document_id,
                        'chunk_id': chunk_id,
                        'metadata': metadata
                    }
                    
                    # Group by document_id
                    if document_id in document_chunks:
                        document_chunks[document_id].append(chunk_data)
                    else:
                        document_chunks[document_id] = [chunk_data]
            
            # Convert grouped chunks to DocumentChunk objects
            for doc_id, chunks in document_chunks.items():
                for chunk_data in chunks:
                    documents.append(DocumentChunk(
                        text=chunk_data['text'],
                        document_id=chunk_data['document_id'],
                        chunk_id=chunk_data['chunk_id'],
                        metadata=chunk_data['metadata']
                    ))
            
            logging.info(f"Extracted {len(documents)} valid chunks from {len(document_chunks)} documents")
            return documents
            
        except Exception as e:
            logging.error(f"Error extracting Dokling chunks: {e}")
            raise ValueError(f"Failed to extract chunks from Dokling data: {e}")
    
    def _extract_document_id_from_chunk(self, chunk: Any, index: int) -> str:
        """Extract or generate document_id from chunk."""
        
        if isinstance(chunk, dict):
            # Try to get document_id from chunk metadata
            doc_id = chunk.get('document_id') or chunk.get('doc_id') or chunk.get('document_name')
            if doc_id:
                return str(doc_id)
        
        elif hasattr(chunk, 'document_id'):
            return str(chunk.document_id)
        elif hasattr(chunk, 'doc_id'):
            return str(chunk.doc_id)
        elif hasattr(chunk, 'document_name'):
            return str(chunk.document_name)
        
        # If no document_id found, use a default one
        return "default_document"
    
    def _extract_chunk_id_from_chunk(self, chunk: Any, index: int) -> str:
        """Extract or generate chunk_id from chunk."""
        
        if isinstance(chunk, dict):
            # Try to get chunk_id from chunk metadata
            chunk_id = chunk.get('chunk_id') or chunk.get('id') or chunk.get('chunk_index')
            if chunk_id:
                return str(chunk_id)
        
        elif hasattr(chunk, 'chunk_id'):
            return str(chunk.chunk_id)
        elif hasattr(chunk, 'id'):
            return str(chunk.id)
        elif hasattr(chunk, 'chunk_index'):
            return str(chunk.chunk_index)
        
        # If no chunk_id found, generate one
        return f"chunk_{index:03d}"
    
    def _extract_chunks_from_dokling_output(self, dokling_data) -> List[Any]:
        """Extract chunks from various Dokling output formats."""
        
        # Handle DataFrame
        if hasattr(dokling_data, 'data') and hasattr(dokling_data.data, 'raw'):
            # Handle DataFrame with 'raw' attribute (common Dokling format)
            return dokling_data.data.raw
        
        elif hasattr(dokling_data, 'data'):
            # Handle DataFrame with 'data' attribute
            if isinstance(dokling_data.data, list):
                return dokling_data.data
            else:
                return [dokling_data.data]
        
        # Handle direct list
        elif isinstance(dokling_data, list):
            return dokling_data
        
        # Handle single item
        else:
            return [dokling_data]
    
    def _extract_text_from_chunk(self, chunk: Any) -> str:
        """Extract text content from a chunk object."""
        
        if isinstance(chunk, dict):
            # Try different possible text field names
            text_fields = ['text', 'content', 'page_content', 'document_text']
            for field in text_fields:
                if field in chunk and chunk[field]:
                    return str(chunk[field])
            
            # If no text field found, try to convert the whole chunk
            return str(chunk)
        
        elif hasattr(chunk, 'text'):
            # Handle object with text attribute
            return str(chunk.text)
        
        elif hasattr(chunk, 'page_content'):
            # Handle object with page_content attribute
            return str(chunk.page_content)
        
        else:
            # Handle string or other types
            return str(chunk)
    
    def _extract_metadata_from_chunk(self, chunk: Any) -> Dict[str, Any]:
        """Extract metadata from a chunk object."""
        
        metadata = {}
        
        if isinstance(chunk, dict):
            # Copy relevant fields as metadata, excluding text fields
            text_fields = ['text', 'content', 'page_content', 'document_text']
            for key, value in chunk.items():
                if key not in text_fields and value is not None:
                    metadata[key] = value
        
        elif hasattr(chunk, '__dict__'):
            # Handle object attributes
            for key, value in chunk.__dict__.items():
                if not key.startswith('_') and value is not None:
                    metadata[key] = value
        
        return metadata
    
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
        
        # Log the payload for debugging
        logging.info(f"Sending {len(documents)} documents to LangExtract API")
        logging.info(f"Document IDs: {[doc.document_id for doc in documents]}")
        logging.info(f"Chunk IDs: {[doc.chunk_id for doc in documents]}")
        
        # Make API request
        url = f"{client['base_url']}/api/process/"
        
        try:
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


# Utility functions for standalone use
def create_langextract_component(api_url: str = "https://langextract.ai-did-it.eu") -> Dict[str, Any]:
    """Factory function to create a LangExtract client instance."""
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
        'timeout': 30
    }


def process_dokling_chunks(
    dokling_chunks: List[Any],
    schemas: List[str],
    api_url: str = "https://langextract.ai-did-it.eu",
    options: Optional[ProcessingOptions] = None
) -> Dict[str, Any]:
    """Convenience function to process Dokling chunks directly."""
    client = create_langextract_component(api_url)
    
    # Convert Dokling chunks to DocumentChunk format
    documents = []
    for i, chunk in enumerate(dokling_chunks):
        if isinstance(chunk, dict):
            text = chunk.get('text', chunk.get('content', str(chunk)))
            chunk_id = chunk.get('id', f"chunk_{i}")
            document_id = chunk.get('document_id', f"doc_{i}")
        elif hasattr(chunk, 'text'):
            text = str(chunk.text)
            chunk_id = getattr(chunk, 'id', f"chunk_{i}")
            document_id = getattr(chunk, 'document_id', f"doc_{i}")
        else:
            text = str(chunk)
            chunk_id = f"chunk_{i}"
            document_id = f"doc_{i}"
        
        if text and text.strip():
            documents.append(DocumentChunk(
                text=text.strip(),
                document_id=str(document_id),
                chunk_id=str(chunk_id)
            ))
    
    # Process documents
    if not options:
        options = ProcessingOptions()
    
    # Prepare payload
    payload = {
        "documents": [asdict(doc) for doc in documents],
        "schemas": schemas,
        "options": asdict(options)
    }
    
    # Make API request
    url = f"{client['base_url']}/api/process/"
    
    try:
        response = client['session'].post(
            url,
            json=payload,
            timeout=client['timeout']
        )
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        logging.error(f"Error processing Dokling chunks: {e}")
        raise RuntimeError(f"Failed to process Dokling chunks: {e}")


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
    print("LangExtract Dokling Component (FIXED VERSION)")
    print("=" * 50)
    
    # Create component
    component = LangExtractComponent()
    
    # Show available schemas
    print("\nAvailable schemas:")
    schemas = [
        "support_case", "refund_case", "invoice", "contract_terms",
        "sop_steps", "price_list", "product_spec", "faq", "policy"
    ]
    for schema in schemas:
        print(f"  - {schema}")
    
    # Show recommended combinations
    print("\nRecommended schema combinations:")
    for combo in get_recommended_schema_combinations():
        print(f"  - {', '.join(combo)}")
    
    print("\nComponent ready for use in Langflow with Dokling!")
    print("Input: Dokling chunks (DoclingDocument)")
    print("Output: Raw LangExtract API response for pipeline integration")
    print("\nNote: To use multiple schemas, separate them with commas (e.g., 'invoice, support_case')")
    print("\nFIXED: Now properly handles multiple chunks from the same document")
