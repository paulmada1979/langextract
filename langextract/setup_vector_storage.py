#!/usr/bin/env python3
"""
Setup script for vector storage integration.
This script helps configure and test the Supabase vector storage setup.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_environment():
    """Check if required environment variables are set."""
    logger.info("🔍 Checking environment configuration...")
    
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
    optional_vars = ['SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_DB_HOST', 'SUPABASE_DB_PASSWORD']
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
    
    if missing_required:
        logger.error(f"❌ Missing required environment variables: {missing_required}")
        return False
    
    if missing_optional:
        logger.warning(f"⚠️ Missing optional environment variables: {missing_optional}")
        logger.info("These are not required for basic functionality but may be needed for migrations.")
    
    logger.info("✅ Environment configuration looks good!")
    return True


def check_dependencies():
    """Check if required Python packages are installed."""
    logger.info("📦 Checking Python dependencies...")
    
    required_packages = [
        'supabase',
        'pgvector',
        'psycopg2',
        'openai',
        'django',
        'djangorestframework'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"❌ Missing required packages: {missing_packages}")
        logger.info("Install them with: pip install -r requirements.txt")
        return False
    
    logger.info("✅ All required packages are installed!")
    return True


def create_env_template():
    """Create a template .env file if it doesn't exist."""
    env_file = '.env'
    
    if os.path.exists(env_file):
        logger.info(f"✅ .env file already exists: {env_file}")
        return True
    
    logger.info("📝 Creating .env template file...")
    
    template_content = """# Django Settings
DEBUG=True
DJANGO_SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# OpenAI API
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=text-embedding-3-small

# Supabase Configuration
SUPABASE_URL=your-supabase-project-url
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# Optional: Direct database connection (for migrations)
SUPABASE_DB_HOST=your-db-host
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your-db-password

# API Settings
API_RATE_LIMIT=1000
MAX_TOKENS_PER_REQUEST=8000
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(template_content)
        
        logger.info(f"✅ Created .env template file: {env_file}")
        logger.info("📝 Please edit this file with your actual credentials")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create .env file: {e}")
        return False


def run_quick_test():
    """Run a quick test to verify the setup."""
    logger.info("🧪 Running quick setup test...")
    
    try:
        # Test basic imports
        from core.processor import document_processor
        from core.vector_storage import vector_storage
        
        logger.info("✅ Core modules imported successfully")
        
        # Test Supabase connection
        try:
            stats = vector_storage.get_storage_stats()
            logger.info(f"✅ Supabase connection successful: {stats.get('status', 'unknown')}")
        except Exception as e:
            logger.warning(f"⚠️ Supabase connection test failed: {e}")
            logger.info("This is expected if you haven't configured credentials yet")
        
        # Test OpenAI connection (if configured)
        try:
            openai_status = document_processor.test_system()
            if openai_status.get('openai_connection'):
                logger.info("✅ OpenAI connection successful")
            else:
                logger.warning("⚠️ OpenAI connection failed - check your API key")
        except Exception as e:
            logger.warning(f"⚠️ OpenAI test failed: {e}")
        
        logger.info("✅ Quick test completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Quick test failed: {e}")
        return False


def print_next_steps():
    """Print next steps for the user."""
    logger.info("\n🚀 Setup completed! Here are your next steps:")
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    
    print("1. 📝 Edit your .env file with your actual credentials:")
    print("   - SUPABASE_URL and SUPABASE_ANON_KEY (required)")
    print("   - OPENAI_API_KEY (for embedding generation)")
    print("   - Other optional settings as needed")
    
    print("\n2. 🗄️ Apply the database migration:")
    print("   python apply_migration.py")
    
    print("\n3. 🧪 Test the complete setup:")
    print("   python test_vector_storage.py")
    
    print("\n4. 🚀 Start your Django server:")
    print("   python manage.py runserver")
    
    print("\n5. 📚 Test the API endpoints:")
    print("   - POST /api/extract/ - Process documents and store embeddings")
    print("   - POST /api/search/ - Search similar documents")
    print("   - GET /api/status/ - Check system health")
    
    print("\n6. 📖 Read the documentation:")
    print("   VECTOR_STORAGE_README.md")
    
    print("\n" + "="*60)
    print("Need help? Check the troubleshooting section in the README")
    print("="*60)


def main():
    """Main setup function."""
    logger.info("🚀 Starting vector storage setup...")
    
    # Load environment variables
    load_dotenv()
    
    # Run setup checks
    checks_passed = True
    
    if not check_environment():
        checks_passed = False
    
    if not check_dependencies():
        checks_passed = False
    
    # Create .env template if needed
    create_env_template()
    
    # Run quick test
    if checks_passed:
        run_quick_test()
    
    # Print next steps
    print_next_steps()
    
    if checks_passed:
        logger.info("🎉 Setup completed successfully!")
        return 0
    else:
        logger.warning("⚠️ Setup completed with warnings - check the output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
