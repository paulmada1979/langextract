"""
Tests for the schema loader module.
"""

import unittest
from unittest.mock import patch, mock_open
from core.schema_loader import SchemaLoader


class TestSchemaLoader(unittest.TestCase):
    """Test cases for SchemaLoader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('core.schema_loader.settings') as mock_settings:
            mock_settings.SCHEMA_DIR = '/fake/schema/path'
            self.loader = SchemaLoader()
    
    @patch('builtins.open', new_callable=mock_open, read_data='schemas:\n  - name: test')
    @patch('pathlib.Path.exists')
    def test_load_registry_success(self, mock_exists, mock_file):
        """Test successful registry loading."""
        mock_exists.return_value = True
        
        with patch('yaml.safe_load') as mock_yaml:
            mock_yaml.return_value = {'schemas': [{'name': 'test'}]}
            result = self.loader._load_registry()
            
            self.assertEqual(result, {'schemas': [{'name': 'test'}]})
    
    @patch('pathlib.Path.exists')
    def test_load_registry_file_not_found(self, mock_exists):
        """Test registry loading when file doesn't exist."""
        mock_exists.return_value = False
        
        result = self.loader._load_registry()
        self.assertEqual(result, {})
    
    def test_list_schemas(self):
        """Test listing available schemas."""
        # Mock the schemas dictionary
        self.loader.schemas = {'test1': {}, 'test2': {}}
        
        schemas = self.loader.list_schemas()
        self.assertEqual(set(schemas), {'test1', 'test2'})
    
    def test_get_schema_existing(self):
        """Test getting an existing schema."""
        test_schema = {'name': 'test', 'fields': {}}
        self.loader.schemas = {'test': test_schema}
        
        result = self.loader.get_schema('test')
        self.assertEqual(result, test_schema)
    
    def test_get_schema_not_found(self):
        """Test getting a non-existent schema."""
        result = self.loader.get_schema('nonexistent')
        self.assertIsNone(result)
    
    def test_validate_schema_references_valid(self):
        """Test schema reference validation with valid references."""
        # Mock a valid schema with enum references
        test_schema = {
            'fields': {
                'currency': {'enum_ref': 'currencies.iso'}
            }
        }
        
        with patch.object(self.loader, 'get_schema') as mock_get_schema:
            mock_get_schema.return_value = test_schema
            
            with patch.object(self.loader, 'get_vocabulary') as mock_get_vocab:
                mock_get_vocab.return_value = {'iso': ['USD', 'EUR']}
                
                result = self.loader.validate_schema_references('test')
                self.assertTrue(result)
    
    def test_validate_schema_references_invalid(self):
        """Test schema reference validation with invalid references."""
        # Mock an invalid schema with enum references
        test_schema = {
            'fields': {
                'currency': {'enum_ref': 'currencies.iso'}
            }
        }
        
        with patch.object(self.loader, 'get_schema') as mock_get_schema:
            mock_get_schema.return_value = test_schema
            
            with patch.object(self.loader, 'get_vocabulary') as mock_get_vocab:
                mock_get_vocab.return_value = None  # Vocabulary not found
                
                result = self.loader.validate_schema_references('test')
                self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
