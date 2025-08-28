

import json

import tiktoken
from docling_core.transforms.chunker import BaseChunker, DocMeta
from docling_core.transforms.chunker.hierarchical_chunker import HierarchicalChunker

from langflow.base.data.docling_utils import extract_docling_documents
from langflow.custom import Component
from langflow.io import DropdownInput, HandleInput, IntInput, MessageTextInput, Output, StrInput
from langflow.schema import Data, DataFrame


class ChunkDoclingDocumentComponent(Component):
    display_name: str = "Chunk DoclingDocument"
    description: str = "Use the DocumentDocument chunkers to split the document into chunks."
    documentation = "https://docling-project.github.io/docling/concepts/chunking/"
    icon = "Docling"
    name = "ChunkDoclingDocument"

    inputs = [
        HandleInput(
            name="data_inputs",
            display_name="Data or DataFrame",
            info="The data with documents to split in chunks.",
            input_types=["Data", "DataFrame"],
            required=True,
        ),
        DropdownInput(
            name="chunker",
            display_name="Chunker",
            options=["HybridChunker", "HierarchicalChunker"],
            info=("Which chunker to use."),
            value="HybridChunker",
            real_time_refresh=True,
        ),
        DropdownInput(
            name="provider",
            display_name="Provider",
            options=["Hugging Face", "OpenAI"],
            info=("Which tokenizer provider."),
            value="Hugging Face",
            show=True,
            real_time_refresh=True,
            advanced=True,
            dynamic=True,
        ),
        StrInput(
            name="hf_model_name",
            display_name="HF model name",
            info=(
                "Model name of the tokenizer to use with the HybridChunker when Hugging Face is chosen as a tokenizer."
            ),
            value="sentence-transformers/all-MiniLM-L6-v2",
            show=True,
            advanced=True,
            dynamic=True,
        ),
        StrInput(
            name="openai_model_name",
            display_name="OpenAI model name",
            info=("Model name of the tokenizer to use with the HybridChunker when OpenAI is chosen as a tokenizer."),
            value="gpt-4o",
            show=False,
            advanced=True,
            dynamic=True,
        ),
        IntInput(
            name="max_tokens",
            display_name="Maximum tokens",
            info=("Maximum number of tokens for the HybridChunker."),
            show=True,
            required=False,
            advanced=True,
            dynamic=True,
        ),
        MessageTextInput(
            name="doc_key",
            display_name="Doc Key",
            info="The key to use for the DoclingDocument column. Try 'text', 'content', or 'document' if 'doc' doesn't work.",
            value="text",
            advanced=True,
        ),
    ]

    outputs = [
        Output(display_name="DataFrame", name="dataframe", method="chunk_documents"),
    ]

    def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None) -> dict:
        if field_name == "chunker":
            provider_type = build_config["provider"]["value"]
            is_hf = provider_type == "Hugging Face"
            is_openai = provider_type == "OpenAI"
            if field_value == "HybridChunker":
                build_config["provider"]["show"] = True
                build_config["hf_model_name"]["show"] = is_hf
                build_config["openai_model_name"]["show"] = is_openai
                build_config["max_tokens"]["show"] = True
            else:
                build_config["provider"]["show"] = False
                build_config["hf_model_name"]["show"] = False
                build_config["openai_model_name"]["show"] = False
                build_config["max_tokens"]["show"] = False
        elif field_name == "provider" and build_config["chunker"]["value"] == "HybridChunker":
            if field_value == "Hugging Face":
                build_config["hf_model_name"]["show"] = True
                build_config["openai_model_name"]["show"] = False
            elif field_value == "OpenAI":
                build_config["hf_model_name"]["show"] = False
                build_config["openai_model_name"]["show"] = True

        return build_config

    def _docs_to_data(self, docs) -> list[Data]:
        return [Data(text=doc.page_content, data=doc.metadata) for doc in docs]

    def _debug_data_structure(self, data_inputs):
        """Debug function to understand the data structure."""
        print(f"Data type: {type(data_inputs)}")
        
        if hasattr(data_inputs, 'data'):
            print(f"Has 'data' attribute: True")
            print(f"Data attribute type: {type(data_inputs.data)}")
            
            if hasattr(data_inputs.data, 'columns'):
                print(f"DataFrame columns: {list(data_inputs.data.columns)}")
            
            if isinstance(data_inputs.data, list) and len(data_inputs.data) > 0:
                print(f"First item type: {type(data_inputs.data[0])}")
                if isinstance(data_inputs.data[0], dict):
                    print(f"First item keys: {list(data_inputs.data[0].keys())}")
        
        if hasattr(data_inputs, '__dict__'):
            print(f"Object attributes: {list(data_inputs.__dict__.keys())}")

    def chunk_documents(self) -> DataFrame:
        # Debug the input data structure
        print("=== DEBUGGING DATA STRUCTURE ===")
        self._debug_data_structure(self.data_inputs)
        print(f"Doc key being used: '{self.doc_key}'")
        print("================================")
        
        # Try to extract documents, but fall back to manual creation if it fails
        documents = None
        
        try:
            # Try to extract documents with the specified doc_key
            documents = extract_docling_documents(self.data_inputs, self.doc_key)
            print(f"Successfully extracted {len(documents)} documents using extract_docling_documents")
            
        except Exception as e:
            print(f"Failed to extract documents with doc_key '{self.doc_key}': {e}")
            
            # Try alternative doc_keys
            alternative_keys = ["text", "content", "document", "page_content"]
            
            for alt_key in alternative_keys:
                if alt_key != self.doc_key:
                    try:
                        print(f"Trying alternative doc_key: '{alt_key}'")
                        documents = extract_docling_documents(self.data_inputs, alt_key)
                        print(f"Successfully extracted {len(documents)} documents with '{alt_key}'")
                        break
                    except Exception as alt_e:
                        print(f"Failed with '{alt_key}': {alt_e}")
                        continue
            
            # If all else fails, create documents manually
            if documents is None:
                print("All doc_keys failed, creating documents manually...")
                try:
                    documents = self._create_documents_manually(self.data_inputs)
                    print(f"Manually created {len(documents)} documents")
                except Exception as manual_e:
                    print(f"Manual creation failed: {manual_e}")
                    # Last resort: create a simple document from the raw data
                    documents = self._create_simple_document(self.data_inputs)
                    print(f"Created simple document as last resort")

        if not documents:
            raise ValueError("No documents found to chunk. Please check your input data.")

        print(f"Final document count: {len(documents)}")

        chunker: BaseChunker
        if self.chunker == "HybridChunker":
            try:
                from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
            except ImportError as e:
                msg = (
                    "HybridChunker is not installed. Please install it with `uv pip install docling-core[chunking] "
                    "or `uv pip install transformers`"
                )
                raise ImportError(msg) from e
            max_tokens: int | None = self.max_tokens if self.max_tokens else None
            if self.provider == "Hugging Face":
                try:
                    from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
                except ImportError as e:
                    msg = (
                        "HuggingFaceTokenizer is not installed."
                        " Please install it with `uv pip install docling-core[chunking]`"
                    )
                    raise ImportError(msg) from e
                tokenizer = HuggingFaceTokenizer.from_pretrained(
                    model_name=self.hf_model_name,
                    max_tokens=max_tokens,
                )
            elif self.provider == "OpenAI":
                try:
                    from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer
                except ImportError as e:
                    msg = (
                        "OpenAITokenizer is not installed."
                        " Please install it with `uv pip install docling-core[chunking]`"
                        " or `uv pip install transformers`"
                    )
                    raise ImportError(msg) from e
                if max_tokens is None:
                    max_tokens = 128 * 1024  # context window length required for OpenAI tokenizers
                tokenizer = OpenAITokenizer(
                    tokenizer=tiktoken.encoding_for_model(self.openai_model_name), max_tokens=max_tokens
                )
            chunker = HybridChunker(
                tokenizer=tokenizer,
            )
        elif self.chunker == "HierarchicalChunker":
            chunker = HierarchicalChunker()

        results: list[Data] = []
        try:
            for doc in documents:
                for chunk in chunker.chunk(dl_doc=doc):
                    enriched_text = chunker.contextualize(chunk=chunk)
                    meta = DocMeta.model_validate(chunk.meta)

                    results.append(
                        Data(
                            data={
                                "text": enriched_text,
                                "document_id": f"{doc.origin.binary_hash}",
                                "doc_items": json.dumps([item.self_ref for item in meta.doc_items]),
                            }
                        )
                    )

        except Exception as e:
            msg = f"Error splitting text: {e}"
            raise TypeError(msg) from e

        return DataFrame(results)
    
    def _create_documents_manually(self, data_inputs):
        """Create documents manually when automatic extraction fails."""
        from docling_core.document import DoclingDocument
        from docling_core.origin import Origin
        
        documents = []
        
        try:
            # Extract text content from the data
            if hasattr(data_inputs, 'data'):
                data = data_inputs.data
            else:
                data = data_inputs
            
            # Handle different data structures
            if isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        # Try to find text content
                        text = item.get('text', item.get('content', str(item)))
                    else:
                        text = str(item)
                    
                    if text and text.strip():
                        # Create a simple document
                        origin = Origin(
                            binary_hash=f"manual_doc_{i}",
                            file_path="manual_document",
                            file_name="manual_document"
                        )
                        
                        doc = DoclingDocument(
                            page_content=text.strip(),
                            origin=origin
                        )
                        documents.append(doc)
            
            elif hasattr(data, 'columns'):
                # Handle DataFrame
                for i, row in data.iterrows():
                    text = str(row.iloc[0]) if len(row) > 0 else ""
                    if text and text.strip():
                        origin = Origin(
                            binary_hash=f"manual_doc_{i}",
                            file_path="manual_document",
                            file_name="manual_document"
                        )
                        
                        doc = DoclingDocument(
                            page_content=text.strip(),
                            origin=origin
                        )
                        documents.append(doc)
            
            else:
                # Handle single item
                text = str(data)
                if text and text.strip():
                    origin = Origin(
                        binary_hash="manual_doc_0",
                        file_path="manual_document",
                        file_name="manual_document"
                    )
                    
                    doc = DoclingDocument(
                        page_content=text.strip(),
                        origin=origin
                    )
                    documents.append(doc)
            
        except Exception as e:
            print(f"Error in manual document creation: {e}")
            raise
        
        return documents
    
    def _create_simple_document(self, data_inputs):
        """Create a simple document as a last resort when everything else fails."""
        from docling_core.document import DoclingDocument
        from docling_core.origin import Origin
        
        try:
            # Try to extract text from the nested structure
            text = self._extract_text_from_nested_data(data_inputs)
            
            if not text:
                text = "No text content found in input data"
            
            # Create a simple document
            origin = Origin(
                binary_hash="simple_doc_0",
                file_path="simple_document",
                file_name="simple_document"
            )
            
            doc = DoclingDocument(
                page_content=text,
                origin=origin
            )
            
            return [doc]
            
        except Exception as e:
            print(f"Error in simple document creation: {e}")
            # Create a minimal document
            origin = Origin(
                binary_hash="minimal_doc_0",
                file_path="minimal_document",
                file_name="minimal_document"
            )
            
            doc = DoclingDocument(
                page_content="Error: Could not extract text from input data",
                origin=origin
            )
            
            return [doc]
    
    def _extract_text_from_nested_data(self, data_inputs):
        """Extract text from nested data structures like artifacts.dataframe.raw."""
        try:
            # Handle the nested structure from your Dokling output
            if hasattr(data_inputs, 'data'):
                data = data_inputs.data
                
                # Check for artifacts.dataframe.raw structure
                if hasattr(data, 'artifacts'):
                    artifacts = data.artifacts
                    if hasattr(artifacts, 'dataframe'):
                        dataframe = artifacts.dataframe
                        if hasattr(dataframe, 'raw') and isinstance(dataframe.raw, list):
                            # Extract text from the raw data
                            texts = []
                            for item in dataframe.raw:
                                if isinstance(item, dict) and 'text' in item:
                                    texts.append(item['text'])
                                else:
                                    texts.append(str(item))
                            return "\n\n".join(texts)
                
                # Check for direct raw attribute
                if hasattr(data, 'raw') and isinstance(data.raw, list):
                    texts = []
                    for item in data.raw:
                        if isinstance(item, dict) and 'text' in item:
                            texts.append(item['text'])
                        else:
                            texts.append(str(item))
                    return "\n\n".join(texts)
                
                # Handle list data
                if isinstance(data, list):
                    texts = []
                    for item in data:
                        if isinstance(item, dict) and 'text' in item:
                            texts.append(item['text'])
                        else:
                            texts.append(str(item))
                    return "\n\n".join(texts)
                
                # Handle DataFrame
                if hasattr(data, 'columns'):
                    texts = []
                    for i, row in data.iterrows():
                        if len(row) > 0:
                            texts.append(str(row.iloc[0]))
                    return "\n\n".join(texts)
            
            # If no nested structure found, try to convert directly
            return str(data_inputs)
            
        except Exception as e:
            print(f"Error extracting text from nested data: {e}")
            return str(data_inputs)
