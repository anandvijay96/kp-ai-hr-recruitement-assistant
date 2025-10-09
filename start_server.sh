#!/bin/bash

# Script to start the FastAPI server with proper environment setup

echo "=== Starting HR Recruitment Assistant Server ==="
echo ""

# Navigate to project directory
cd /mnt/c/Users/HP/kp-ai-hr-recruitement-assistant

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Verify we're in the venv
echo "Python location: $(which python)"
echo "Pip location: $(which pip)"
echo ""

# Install critical dependencies
echo "Installing critical dependencies..."
pip install --upgrade pip setuptools wheel
pip install fastapi uvicorn[standard] python-multipart aiofiles jinja2 pydantic pydantic-settings sqlalchemy aiosqlite redis email-validator bcrypt PyJWT passlib python-docx PyPDF2 pdfplumber

# Verify FastAPI is installed
echo ""
echo "Verifying installation..."
python -c "import fastapi; import uvicorn; import bcrypt; print('✓ All core packages installed')" || {
    echo "❌ Installation failed. Please check the error above."
    exit 1
}

echo ""
echo "=== Starting server on http://127.0.0.1:8000 ==="
echo "Press CTRL+C to stop the server"
echo ""

# IMPORTANT: Use python -m uvicorn to ensure it uses the venv's Python
python -m uvicorn main:app --reload
