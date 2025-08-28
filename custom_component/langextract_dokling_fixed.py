"""
LangExtract Custom Component for Langflow - Dokling Integration

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
        
        Dokling chunks typically have this structure:
        - text: The chunk text content
        - id: Unique chunk identifier
        - document_id: Document identifier
        - metadata: Additional chunk metadata
        """
        documents = []
        
        try:
            # Handle different possible Dokling data structures
            if hasattr(dokling_data, 'data'):
                chunks_data = dokling_data.data
            else:
                chunks_data = dokling_data
            
            # Convert to list if it's not already
            if not isinstance(chunks_data, list):
                chunks_data = [chunks_data]
            
            for i, chunk in enumerate(chunks_data):
                # Handle different chunk formats
                if isinstance(chunk, dict):
                    # Extract text content
                    text = chunk.get('text', chunk.get('content', str(chunk)))
                    
                    # Extract or generate IDs
                    chunk_id = chunk.get('id', chunk.get('chunk_id', f"chunk_{i}"))
                    document_id = chunk.get('document_id', chunk.get('doc_id', f"doc_{i}"))
                    
                    # Extract metadata
                    metadata = chunk.get('metadata', {})
                    if not metadata and isinstance(chunk, dict):
                        # Copy relevant fields as metadata
                        metadata = {k: v for k, v in chunk.items() 
                                  if k not in ['text', 'content', 'id', 'chunk_id', 'document_id', 'doc_id']}
                    
                elif hasattr(chunk, 'text'):
                    # Handle object with text attribute
                    text = str(chunk.text)
                    chunk_id = getattr(chunk, 'id', f"chunk_{i}")
                    document_id = getattr(chunk, 'document_id', f"doc_{i}")
                    metadata = {}
                    
                else:
                    # Handle string or other types
                    text = str(chunk)
                    chunk_id = f"chunk_{i}"
                    document_id = f"doc_{i}"
                    metadata = {}
                
                # Validate text content
                if text and text.strip():
                    documents.append(DocumentChunk(
                        text=text.strip(),
                        document_id=str(document_id),
                        chunk_id=str(chunk_id),
                        metadata=metadata
                    ))
            
            logging.info(f"Extracted {len(documents)} valid chunks from Dokling output")
            return documents
            
        except Exception as e:
            logging.error(f"Error extracting Dokling chunks: {e}")
            raise ValueError(f"Failed to extract chunks from Dokling data: {e}")
    
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
            logging.info(f"Processing {len(documents)} Dokling chunks with schemas: {schemas}")
            response = client['session'].post(
                url,
                json=payload,
                timeout=client['timeout']
            )
            response.raise_for_status()
            
            result = response.json()
            logging.info(f"Successfully processed {len(documents)} Dokling chunks")
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
    print("LangExtract Dokling Component")
    print("=" * 40)
    
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

