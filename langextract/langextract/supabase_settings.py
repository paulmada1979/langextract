"""
Supabase configuration settings for the langextract project.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase Configuration
SUPABASE_CONFIG = {
    'url': os.getenv('SUPABASE_URL'),
    'anon_key': os.getenv('SUPABASE_ANON_KEY'),
    'service_role_key': os.getenv('SUPABASE_SERVICE_ROLE_KEY'),
}

# Vector Database Configuration
VECTOR_CONFIG = {
    'table_name': 'embeddings',
    'embedding_dimension': 1536,  # OpenAI text-embedding-3-small
    'similarity_threshold': 0.7,
    'max_search_results': 100,
}

# Database Connection Settings
DB_CONFIG = {
    'host': os.getenv('SUPABASE_DB_HOST'),
    'port': os.getenv('SUPABASE_DB_PORT', '5432'),
    'database': os.getenv('SUPABASE_DB_NAME'),
    'user': os.getenv('SUPABASE_DB_USER'),
    'password': os.getenv('SUPABASE_DB_PASSWORD'),
}

# Validation
def validate_supabase_config():
    """Validate that required Supabase configuration is present."""
    required_keys = ['url', 'anon_key']
    missing_keys = [key for key in required_keys if not SUPABASE_CONFIG.get(key)]
    
    if missing_keys:
        raise ValueError(f"Missing required Supabase configuration: {missing_keys}")
    
    return True

# Test configuration on import
try:
    validate_supabase_config()
except ValueError as e:
    print(f"Warning: Supabase configuration incomplete: {e}")
    print("Vector storage features will not work without proper configuration.")
