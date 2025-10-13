#!/bin/bash

# Script to install all dependencies in virtual environment

echo "=== Installing Dependencies for HR Recruitment Assistant ==="
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

echo "Installing core dependencies..."
pip install --upgrade pip

# Install dependencies in groups to handle errors better
echo ""
echo "1/5 Installing FastAPI and web framework..."
pip install fastapi uvicorn[standard] python-multipart aiofiles jinja2

echo ""
echo "2/5 Installing data validation and settings..."
pip install pydantic pydantic-settings email-validator

echo ""
echo "3/5 Installing database dependencies..."
pip install sqlalchemy aiosqlite redis asyncpg

echo ""
echo "4/5 Installing authentication dependencies..."
pip install bcrypt PyJWT passlib

echo ""
echo "5/5 Installing document processing (may take time)..."
pip install python-docx docx2txt docxtpl PyPDF2 pdfplumber

echo ""
echo "Installing remaining dependencies..."
pip install pytest pytest-asyncio httpx sendgrid

echo ""
echo "=== Installation Complete ==="
echo ""
echo "To start the server, run:"
echo "  source venv/bin/activate"
echo "  uvicorn main:app --reload"
echo ""
echo "Or simply run: bash start_server.sh"
