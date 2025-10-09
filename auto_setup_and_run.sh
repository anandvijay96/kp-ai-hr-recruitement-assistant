#!/bin/bash

# ============================================
# AUTOMATIC SETUP AND RUN SCRIPT
# ============================================
# This script does EVERYTHING automatically

set -e  # Exit on error

echo "============================================"
echo "  HR Recruitment System - Auto Setup"
echo "============================================"
echo ""

# Navigate to project
cd /mnt/c/Users/HP/kp-ai-hr-recruitement-assistant

echo "Step 1/6: Cleaning up old virtual environment..."
rm -rf venv
echo "✓ Done"
echo ""

echo "Step 2/6: Creating fresh virtual environment..."
python3 -m venv venv
echo "✓ Done"
echo ""

echo "Step 3/6: Activating virtual environment..."
source venv/bin/activate
echo "✓ Done"
echo ""

echo "Step 4/6: Installing all dependencies..."
pip install --upgrade pip setuptools wheel --quiet
pip install fastapi uvicorn[standard] python-multipart aiofiles jinja2 pydantic pydantic-settings sqlalchemy aiosqlite redis email-validator bcrypt PyJWT passlib python-docx PyPDF2 pdfplumber --quiet

# Verify installation
python -c "import fastapi; import uvicorn; import bcrypt" && echo "✓ All packages installed successfully" || {
    echo "❌ Installation failed!"
    exit 1
}
echo ""

echo "Step 5/6: Applying database migration..."
python apply_migration.py migrations/010_create_user_management_tables.sql
echo ""

echo "Step 6/6: Creating initial admin user..."
python create_admin_user.py
echo ""

echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "🚀 Starting server now..."
echo ""
echo "Server will be available at:"
echo "  → http://localhost:8000"
echo "  → http://localhost:8000/register (to create account)"
echo "  → http://localhost:8000/login (to login)"
echo "  → http://localhost:8000/users (user management)"
echo ""
echo "Press CTRL+C to stop the server"
echo "============================================"
echo ""

# Start server using python -m to ensure correct environment
python -m uvicorn main:app --reload
