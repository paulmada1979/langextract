#!/bin/bash

# LangExtract Chat API Startup Script

echo "🚀 Starting LangExtract Chat API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📥 Installing requirements..."
pip install -r chat_requirements.txt

# Check environment variables
echo "🔍 Checking environment variables..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY is not set!"
    echo "Please set it with: export OPENAI_API_KEY='your-key-here'"
    exit 1
fi

if [ -z "$SUPABASE_URL" ]; then
    echo "❌ SUPABASE_URL is not set!"
    echo "Please set it with: export SUPABASE_URL='https://your-project.supabase.co'"
    exit 1
fi

if [ -z "$SUPABASE_SERVICE_KEY" ]; then
    echo "❌ SUPABASE_SERVICE_KEY is not set!"
    echo "Please set it with: export SUPABASE_SERVICE_KEY='your-service-key-here'"
    exit 1
fi

echo "✅ Environment variables are set"

# Start the API
echo "🌐 Starting Chat API on http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🖥️  Web Interface: Open chat_interface.html in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python chat_api.py --host 0.0.0.0 --port 8000

