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
pip install --quiet fastapi uvicorn[standard] python-multipart aiofiles jinja2 pydantic pydantic-settings sqlalchemy aiosqlite redis email-validator bcrypt PyJWT passlib python-docx PyPDF2 pdfplumber

echo ""
echo "=== Starting server on http://127.0.0.1:8000 ==="
echo "Press CTRL+C to stop the server"
echo ""

# Start the server
uvicorn main:app --reload
