#!/usr/bin/env python3
"""
Chat API for LangExtract Embeddings
This API allows you to chat with your documents stored in Supabase using OpenAI.

Usage:
    python chat_api.py

API Endpoints:
    POST /chat - Chat with documents
    GET /health - Health check
    GET /stats - Get embedding statistics
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import openai
import psycopg2
from psycopg2.extras import RealDictCursor
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LangExtract Chat API",
    description="Chat with your documents using OpenAI and Supabase embeddings",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "langextract")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Validate required environment variables
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is required")
if not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_SERVICE_KEY environment variable is required")

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY

# Pydantic models
class ChatMessage(BaseModel):
    message: str = Field(..., description="The user's message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context")
    max_results: int = Field(5, ge=1, le=20, description="Maximum number of relevant documents to retrieve")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity threshold for document retrieval")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="OpenAI temperature for response generation")
    model: str = Field("gpt-4o-mini", description="OpenAI model to use")

class ChatResponse(BaseModel):
    response: str = Field(..., description="The AI's response")
    sources: List[Dict[str, Any]] = Field(..., description="Source documents used for the response")
    conversation_id: str = Field(..., description="Conversation ID for context")
    timestamp: datetime = Field(..., description="Response timestamp")

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    openai_connected: bool
    database_connected: bool
    total_embeddings: int

class StatsResponse(BaseModel):
    total_embeddings: int
    unique_documents: int
    unique_chunks: int
    latest_embedding: Optional[datetime]
    oldest_embedding: Optional[datetime]

# Database connection
def get_db_connection():
    """Get database connection."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

# Utility functions
def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text using OpenAI."""
    try:
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate embedding")

def search_similar_documents(
    query_embedding: List[float], 
    max_results: int = 5, 
    similarity_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """Search for similar documents in the database."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Convert embedding to PostgreSQL vector format
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        # Search using the match_documents function
        cursor.execute("""
            SELECT 
                id,
                chunk_id,
                document_id,
                content,
                similarity
            FROM match_documents(
                %s::vector(1536),
                %s,
                %s
            )
        """, (embedding_str, similarity_threshold, max_results))
        
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        documents = []
        for row in results:
            documents.append({
                "id": str(row["id"]),
                "chunk_id": row["chunk_id"],
                "document_id": row["document_id"],
                "content": row["content"],
                "similarity": float(row["similarity"])
            })
        
        return documents
        
    except Exception as e:
        logger.error(f"Database search failed: {e}")
        raise HTTPException(status_code=500, detail="Database search failed")
    finally:
        if conn:
            conn.close()

def generate_chat_response(
    user_message: str,
    relevant_docs: List[Dict[str, Any]],
    model: str = "gpt-4o-mini",
    temperature: float = 0.7
) -> str:
    """Generate chat response using OpenAI."""
    try:
        # Prepare context from relevant documents
        context = ""
        for i, doc in enumerate(relevant_docs, 1):
            context += f"Document {i} (Similarity: {doc['similarity']:.3f}):\n"
            context += f"Content: {doc['content']}\n"
            context += f"Source: {doc['document_id']} - {doc['chunk_id']}\n\n"
        
        # Create the prompt
        system_prompt = """You are a helpful AI assistant that answers questions based on the provided document context. 
        
Instructions:
1. Answer the user's question using ONLY the information provided in the context documents
2. If the context doesn't contain enough information to answer the question, say so clearly
3. Cite the relevant document sources when providing information
4. Be concise but comprehensive in your responses
5. If multiple documents contain relevant information, synthesize the information coherently

Context Documents:
{context}

User Question: {question}

Please provide a helpful response based on the context above."""

        prompt = system_prompt.format(
            context=context,
            question=user_message
        )
        
        # Generate response using OpenAI
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant that answers questions based on provided document context."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Failed to generate chat response: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate chat response")

# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check OpenAI connection
        openai_connected = False
        try:
            openai.models.list()
            openai_connected = True
        except:
            pass
        
        # Check database connection
        database_connected = False
        total_embeddings = 0
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM embeddings")
            total_embeddings = cursor.fetchone()[0]
            database_connected = True
            conn.close()
        except:
            pass
        
        return HealthResponse(
            status="healthy" if openai_connected and database_connected else "unhealthy",
            timestamp=datetime.now(),
            openai_connected=openai_connected,
            database_connected=database_connected,
            total_embeddings=total_embeddings
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get embedding statistics."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total embeddings
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        total_embeddings = cursor.fetchone()[0]
        
        # Get unique documents
        cursor.execute("SELECT COUNT(DISTINCT document_id) FROM embeddings")
        unique_documents = cursor.fetchone()[0]
        
        # Get unique chunks
        cursor.execute("SELECT COUNT(DISTINCT chunk_id) FROM embeddings")
        unique_chunks = cursor.fetchone()[0]
        
        # Get latest and oldest embeddings
        cursor.execute("""
            SELECT 
                MIN(created_at) as oldest,
                MAX(created_at) as latest
            FROM embeddings
        """)
        result = cursor.fetchone()
        oldest_embedding = result[0] if result[0] else None
        latest_embedding = result[1] if result[1] else None
        
        return StatsResponse(
            total_embeddings=total_embeddings,
            unique_documents=unique_documents,
            unique_chunks=unique_chunks,
            latest_embedding=latest_embedding,
            oldest_embedding=oldest_embedding
        )
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")
    finally:
        if conn:
            conn.close()

@app.post("/chat", response_model=ChatResponse)
async def chat_with_documents(chat_message: ChatMessage):
    """Chat with documents using embeddings search."""
    try:
        logger.info(f"Processing chat message: {chat_message.message[:100]}...")
        
        # Generate embedding for the user's message
        query_embedding = generate_embedding(chat_message.message)
        
        # Search for similar documents
        relevant_docs = search_similar_documents(
            query_embedding=query_embedding,
            max_results=chat_message.max_results,
            similarity_threshold=chat_message.similarity_threshold
        )
        
        logger.info(f"Found {len(relevant_docs)} relevant documents")
        
        # Generate chat response
        response_text = generate_chat_response(
            user_message=chat_message.message,
            relevant_docs=relevant_docs,
            model=chat_message.model,
            temperature=chat_message.temperature
        )
        
        # Generate conversation ID if not provided
        conversation_id = chat_message.conversation_id or f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return ChatResponse(
            response=response_text,
            sources=relevant_docs,
            conversation_id=conversation_id,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "LangExtract Chat API",
        "version": "1.0.0",
        "endpoints": {
            "POST /chat": "Chat with documents",
            "GET /health": "Health check",
            "GET /stats": "Get embedding statistics",
            "GET /": "This information"
        },
        "documentation": "https://langextract.ai-did-it.eu"
    }

# Main function
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LangExtract Chat API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    logger.info("Starting LangExtract Chat API...")
    logger.info(f"OpenAI API Key: {'✓' if OPENAI_API_KEY else '✗'}")
    logger.info(f"Supabase URL: {'✓' if SUPABASE_URL else '✗'}")
    logger.info(f"Database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    uvicorn.run(
        "chat_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )

