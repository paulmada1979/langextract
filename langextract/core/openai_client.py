"""
OpenAI API client for generating embeddings and handling API calls.
"""

import logging
import time
from typing import List, Dict, Any, Optional
import openai
from django.conf import settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Handles OpenAI API interactions for embedding generation."""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.MAX_TOKENS_PER_REQUEST
        
        if not self.api_key:
            logger.warning("OpenAI API key not configured - embeddings will not be generated")
            self.client = None
        else:
            try:
                # Set the API key for the older openai library
                openai.api_key = self.api_key
                self.client = openai
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        
        self.rate_limit_delay = 0.1  # 100ms delay between requests
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text string.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not self.client:
            logger.warning("OpenAI client not available - cannot generate embeddings")
            return None
        
        try:
            # Add delay for rate limiting
            time.sleep(self.rate_limit_delay)
            
            response = self.client.Embedding.create(
                model=self.model,
                input=text
            )
            
            embedding = response['data'][0]['embedding']
            logger.debug(f"Generated embedding for text (length: {len(text)})")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in a batch.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (None for failed embeddings)
        """
        embeddings = []
        
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
        
        return embeddings
    
    def validate_text_length(self, text: str) -> bool:
        """
        Validate that text length is within OpenAI's token limits.
        
        Args:
            text: Text to validate
            
        Returns:
            True if text is within limits
        """
        # Rough estimation: 1 token ≈ 4 characters
        estimated_tokens = len(text) / 4
        return estimated_tokens <= self.max_tokens
    
    def truncate_text(self, text: str, max_tokens: Optional[int] = None) -> str:
        """
        Truncate text to fit within token limits.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum tokens allowed (defaults to settings)
            
        Returns:
            Truncated text
        """
        if max_tokens is None:
            max_tokens = self.max_tokens
        
        # Rough estimation: 1 token ≈ 4 characters
        max_chars = max_tokens * 4
        
        if len(text) <= max_chars:
            return text
        
        # Truncate and add ellipsis
        truncated = text[:max_chars-3] + "..."
        logger.warning(f"Text truncated from {len(text)} to {len(truncated)} characters")
        return truncated
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current embedding model."""
        return {
            'model': self.model,
            'max_tokens': self.max_tokens,
            'rate_limit_delay': self.rate_limit_delay
        }
    
    def test_connection(self) -> bool:
        """Test the OpenAI API connection."""
        if not self.client:
            return False
        
        try:
            # Try to generate a simple embedding
            test_text = "test"
            embedding = self.generate_embedding(test_text)
            return embedding is not None
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False


# Global OpenAI client instance
openai_client = OpenAIClient()
