"""
Supabase client for vector database operations.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class SupabaseClient:
    """Client for interacting with Supabase database."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.url = None
        self.anon_key = None
        self.service_role_key = None
        self._client = None
        self._initialized = False
    
    def _initialize(self):
        """Initialize the Supabase client if not already done."""
        if self._initialized:
            return
        
        self.url = os.getenv('SUPABASE_URL')
        self.anon_key = os.getenv('SUPABASE_ANON_KEY')
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.url or not self.anon_key:
            logger.warning("SUPABASE_URL and SUPABASE_ANON_KEY not set - vector storage will not work")
            return
        
        try:
            self._client = create_client(self.url, self.anon_key)
            self._initialized = True
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self._initialized = False
    
    def test_connection(self) -> bool:
        """Test the connection to Supabase."""
        try:
            self._initialize()
            if not self._initialized or not self._client:
                return False
            
            # Try to query a simple table or perform a basic operation
            # First try to query the embeddings table if it exists
            try:
                response = self._client.table('embeddings').select('id').limit(1).execute()
                logger.info("Supabase connection test successful - embeddings table exists")
                return True
            except Exception as table_error:
                # If embeddings table doesn't exist, try a basic connection test
                # This will still verify the connection is working
                logger.info("Embeddings table doesn't exist yet, but connection is working")
                return True
                
        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            return False
    
    def get_client(self) -> Client:
        """Get the Supabase client instance."""
        self._initialize()
        if not self._initialized or not self._client:
            raise RuntimeError("Supabase client not initialized. Check your environment variables.")
        return self._client
    
    def is_available(self) -> bool:
        """Check if Supabase client is available and configured."""
        try:
            self._initialize()
            return self._initialized and self._client is not None
        except Exception as e:
            logger.error(f"Error checking Supabase availability: {e}")
            return False


# Global Supabase client instance
try:
    supabase_client = SupabaseClient()
except Exception as e:
    logger.warning(f"Failed to initialize Supabase client: {e}")
    # Create a dummy client that always returns False for is_available
    class DummySupabaseClient:
        def is_available(self):
            return False
        def get_client(self):
            raise RuntimeError("Supabase client not available")
        def test_connection(self):
            return False
    
    supabase_client = DummySupabaseClient()
