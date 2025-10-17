#!/bin/bash

# ============================================
# AI HR Assistant - Local Development Setup Script
# ============================================
# This script helps set up the complete development environment
# Run this script in the project root directory

set -e  # Exit on any error

echo "🚀 AI HR Assistant - Local Development Setup"
echo "============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
else
    echo "⚠️  Warning: No virtual environment detected."
    echo "   Consider creating one: python3 -m venv venv"
    echo "   And activating it: source venv/bin/activate"
    echo ""
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create necessary directories
echo ""
echo "📁 Creating required directories..."
mkdir -p uploads/resumes
mkdir -p uploads/temp
mkdir -p logs
mkdir -p results
mkdir -p temp/vetting_sessions
mkdir -p temp/vetting_files

echo "✅ Directories created"

# Set proper permissions
echo ""
echo "🔐 Setting directory permissions..."
chmod -R 755 uploads/ logs/ results/ temp/

echo "✅ Permissions set"

# Initialize database
echo ""
echo "🗄️  Initializing database..."
echo "   This will create all necessary tables and relationships."

# Run database migrations
python -m alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Database initialized successfully"
else
    echo "❌ Database initialization failed"
    echo "   Check your database configuration in .env"
    exit 1
fi

# Check for required environment variables
echo ""
echo "🔍 Checking environment configuration..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env from template"
    echo "   ⚠️  IMPORTANT: Edit .env file and add your API keys!"
else
    echo "✅ .env file exists"
fi

# Check for Gemini API key
if grep -q "GEMINI_API_KEY=your_gemini_api_key_here" .env; then
    echo "⚠️  Gemini API key not configured"
    echo "   Please get your API key from: https://makersuite.google.com/app/apikey"
    echo "   Update GEMINI_API_KEY in your .env file"
else
    echo "✅ Gemini API key configured"
fi

# Optional: Check for OpenAI API key
if grep -q "OPENAI_API_KEY=$" .env || grep -q "OPENAI_API_KEY=your_openai_api_key_here" .env; then
    echo "ℹ️  OpenAI API key not configured (optional fallback)"
else
    echo "✅ OpenAI API key configured"
fi

# Test database connection
echo ""
echo "🔗 Testing database connection..."
python -c "
try:
    from core.database import engine
    with engine.connect() as conn:
        result = conn.execute('SELECT 1')
        print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    print('   Check your DATABASE_URL in .env')
    exit(1)
"

# Test LLM configuration
echo ""
echo "🤖 Testing LLM configuration..."
python -c "
import os
from services.llm_resume_extractor import LLMResumeExtractor

try:
    extractor = LLMResumeExtractor()
    print('✅ LLM configuration successful')
    print(f'   Provider: {extractor.provider}')
    print(f'   Model: {extractor.model.model_name}')
except Exception as e:
    print(f'⚠️  LLM configuration issue: {e}')
    print('   This is expected if API keys are not configured yet')
"

echo ""
echo "🎯 Setup Summary:"
echo "================"

# Check what's ready vs what needs configuration
READY_ITEMS=()
TODO_ITEMS=()

# Database check
python -c "
from core.database import engine
try:
    with engine.connect() as conn:
        conn.execute('SELECT 1')
        print('✅ Database: Connected and ready')
except:
    print('❌ Database: Not connected')
" 2>/dev/null && READY_ITEMS+=("Database") || TODO_ITEMS+=("Database setup")

# Dependencies check
if pip list | grep -q "fastapi\|sqlalchemy\|google-generativeai"; then
    echo "✅ Dependencies: Installed"
    READY_ITEMS+=("Dependencies")
else
    echo "❌ Dependencies: Not installed"
    TODO_ITEMS+=("Install dependencies")
fi

# Environment file check
if [ -f ".env" ]; then
    echo "✅ Environment file: Exists"
    READY_ITEMS+=("Environment file")
else
    echo "❌ Environment file: Missing"
    TODO_ITEMS+=("Create .env file")
fi

# Gemini API key check
if ! grep -q "GEMINI_API_KEY=your_gemini_api_key_here" .env 2>/dev/null; then
    echo "✅ Gemini API: Configured"
    READY_ITEMS+=("Gemini API")
else
    echo "⚠️  Gemini API: Needs configuration"
    TODO_ITEMS+=("Configure Gemini API key")
fi

echo ""
echo "📋 Setup Status:"
echo "================"
echo "✅ Ready (${#READY_ITEMS[@]} items):"
for item in "${READY_ITEMS[@]}"; do
    echo "   • $item"
done

if [ ${#TODO_ITEMS[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  Needs Attention (${#TODO_ITEMS[@]} items):"
    for item in "${TODO_ITEMS[@]}"; do
        echo "   • $item"
    done
fi

echo ""
echo "🚀 Next Steps:"
echo "=============="

if [ ${#TODO_ITEMS[@]} -eq 0 ]; then
    echo "🎉 You're all set! Run the application:"
    echo "   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    echo ""
    echo "   Visit: http://localhost:8000"
else
    echo "1. Configure your API keys in .env file"
    echo "2. Run: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    echo "3. Visit: http://localhost:8000"
fi

echo ""
echo "📚 Additional Resources:"
echo "======================="
echo "• Complete setup guide: README_LOCAL_SETUP.md"
echo "• API documentation: http://localhost:8000/docs (after starting)"
echo "• Troubleshooting: See README_LOCAL_SETUP.md"
echo ""
echo "💡 Tips:"
echo "• Use SQLite for quick development (no database setup needed)"
echo "• PostgreSQL recommended for full feature compatibility"
echo "• Get Gemini API key from: https://makersuite.google.com/app/apikey"
echo ""
echo "✅ Setup script completed!"
