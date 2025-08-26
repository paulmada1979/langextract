"""
Schema loader module for managing and loading schemas from the schemas directory.
"""

import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class SchemaLoader:
    """Handles loading and managing schemas from the schemas directory."""
    
    def __init__(self):
        self.schema_dir = Path(settings.SCHEMA_DIR)
        self.registry = self._load_registry()
        self.schemas = {}
        self.vocabularies = {}
        self._load_all_schemas()
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load the schema registry from registry.yaml."""
        registry_path = self.schema_dir / 'registry.yaml'
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Registry file not found: {registry_path}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing registry: {e}")
            return {}
    
    def _load_all_schemas(self):
        """Load all schemas and vocabularies."""
        self._load_vocabularies()
        self._load_core_schemas()
        self._load_domain_schemas()
    
    def _load_vocabularies(self):
        """Load vocabulary files from schemas-vocab directory."""
        vocab_dir = self.schema_dir / 'schemas-vocab'
        if not vocab_dir.exists():
            return
        
        for vocab_file in vocab_dir.glob('*.yaml'):
            try:
                with open(vocab_file, 'r', encoding='utf-8') as f:
                    vocab_name = vocab_file.stem
                    self.vocabularies[vocab_name] = yaml.safe_load(f)
                    logger.info(f"Loaded vocabulary: {vocab_name}")
            except Exception as e:
                logger.error(f"Error loading vocabulary {vocab_file}: {e}")
        
        for vocab_file in vocab_dir.glob('*.json'):
            try:
                with open(vocab_file, 'r', encoding='utf-8') as f:
                    vocab_name = vocab_file.stem
                    self.vocabularies[vocab_name] = json.load(f)
                    logger.info(f"Loaded vocabulary: {vocab_name}")
            except Exception as e:
                logger.error(f"Error loading vocabulary {vocab_file}: {e}")
    
    def _load_core_schemas(self):
        """Load core schemas from schemas-core directory."""
        core_dir = self.schema_dir / 'schemas-core'
        if not core_dir.exists():
            return
        
        for schema_file in core_dir.glob('*.json'):
            try:
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema_name = schema_file.stem
                    self.schemas[schema_name] = json.load(f)
                    logger.info(f"Loaded core schema: {schema_name}")
            except Exception as e:
                logger.error(f"Error loading core schema {schema_file}: {e}")
    
    def _load_domain_schemas(self):
        """Load domain-specific schemas from schemas-domains directory."""
        domain_dir = self.schema_dir / 'schemas-domains'
        if not domain_dir.exists():
            return
        
        for domain_subdir in domain_dir.iterdir():
            if domain_subdir.is_dir():
                domain_name = domain_subdir.name
                for schema_file in domain_subdir.glob('*.json'):
                    try:
                        with open(schema_file, 'r', encoding='utf-8') as f:
                            schema_name = f"{schema_file.stem}.{domain_name}"
                            self.schemas[schema_name] = json.load(f)
                            logger.info(f"Loaded domain schema: {schema_name}")
                    except Exception as e:
                        logger.error(f"Error loading domain schema {schema_file}: {e}")
    
    def get_schema(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific schema by name."""
        return self.schemas.get(schema_name)
    
    def get_vocabulary(self, vocab_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific vocabulary by name."""
        return self.vocabularies.get(vocab_name)
    
    def list_schemas(self) -> List[str]:
        """List all available schema names."""
        return list(self.schemas.keys())
    
    def list_vocabularies(self) -> List[str]:
        """List all available vocabulary names."""
        return list(self.vocabularies.keys())
    
    def get_registry(self) -> Dict[str, Any]:
        """Get the schema registry."""
        return self.registry
    
    def validate_schema_references(self, schema_name: str) -> bool:
        """Validate that a schema's references are valid."""
        schema = self.get_schema(schema_name)
        if not schema:
            return False
        
        # Check for enum references
        if 'fields' in schema:
            for field_name, field_def in schema['fields'].items():
                if 'enum_ref' in field_def:
                    vocab_name, enum_name = field_def['enum_ref'].split('.')
                    vocab = self.get_vocabulary(vocab_name)
                    if not vocab or enum_name not in vocab:
                        logger.warning(f"Invalid enum reference in {schema_name}.{field_name}: {field_def['enum_ref']}")
                        return False
        
        return True


# Global schema loader instance
schema_loader = SchemaLoader()
