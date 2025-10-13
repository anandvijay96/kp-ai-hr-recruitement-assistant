#!/bin/bash

# Setup script for HR Recruitment Assistant
# This script installs all required dependencies and prepares the environment

echo "=================================="
echo "HR Recruitment System - Setup"
echo "=================================="
echo ""

# Navigate to project directory
cd /mnt/c/Users/HP/kp-ai-hr-recruitement-assistant

# Update package list
echo "Step 1: Updating package list..."
sudo apt update

# Install Python pip and venv
echo "Step 2: Installing Python pip and venv..."
sudo apt install -y python3-pip python3-venv

# Remove old virtual environment if corrupted
echo "Step 3: Checking virtual environment..."
if [ -d ".venv" ]; then
    echo "Removing old virtual environment..."
    rm -rf .venv
fi

# Create new virtual environment
echo "Step 4: Creating new virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "Step 5: Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Step 6: Upgrading pip..."
pip install --upgrade pip

# Install all requirements
echo "Step 7: Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# If requirements.txt fails, install manually
if [ $? -ne 0 ]; then
    echo "Step 7b: Installing dependencies manually..."
    pip install fastapi uvicorn sqlalchemy pydantic python-multipart aiofiles bcrypt python-jose passlib pydantic-settings redis python-dotenv aiosqlite email-validator
fi

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "To start the server, run:"
echo "  source .venv/bin/activate"
echo "  uvicorn main:app --reload"
echo ""
