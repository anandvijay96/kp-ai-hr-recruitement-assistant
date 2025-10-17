# ============================================
# AI HR Assistant - Local Development Setup Script (Windows)
# ============================================
# This script helps set up the complete development environment on Windows
# Run this script in PowerShell as Administrator

Write-Host "🚀 AI HR Assistant - Local Development Setup (Windows)" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>$null
    if ($pythonVersion -match "Python (\d+\.\d+)") {
        $version = [double]$matches[1]
        if ($version -ge 3.8) {
            Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
        } else {
            Write-Host "❌ Python $pythonVersion is too old. Please install Python 3.8 or higher." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "❌ Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
$venvPath = "venv"
if (Test-Path $venvPath) {
    Write-Host "✅ Virtual environment detected: $venvPath" -ForegroundColor Green
} else {
    Write-Host "⚠️  Warning: No virtual environment detected." -ForegroundColor Yellow
    Write-Host "   Consider creating one: python -m venv venv" -ForegroundColor Yellow
    Write-Host "   And activating it: venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host ""
}

# Install Python dependencies
Write-Host ""
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Cyan
try {
    pip install -r requirements.txt
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Create necessary directories
Write-Host ""
Write-Host "📁 Creating required directories..." -ForegroundColor Cyan
$directories = @(
    "uploads\resumes",
    "uploads\temp",
    "logs",
    "results",
    "temp\vetting_sessions",
    "temp\vetting_files"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "   ✅ Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "   ✅ Exists: $dir" -ForegroundColor Green
    }
}

# Set proper permissions (Windows equivalent)
Write-Host ""
Write-Host "🔐 Setting directory permissions..." -ForegroundColor Cyan
try {
    # On Windows, we don't need to set permissions like Unix
    # Files inherit permissions from parent directory
    Write-Host "✅ Permissions set (Windows default)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not set permissions: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Initialize database
Write-Host ""
Write-Host "🗄️  Initializing database..." -ForegroundColor Cyan
Write-Host "   This will create all necessary tables and relationships." -ForegroundColor Cyan

try {
    python -m alembic upgrade head
    Write-Host "✅ Database initialized successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Database initialization failed" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Check your database configuration in .env" -ForegroundColor Red
    exit 1
}

# Check for required environment variables
Write-Host ""
Write-Host "🔍 Checking environment configuration..." -ForegroundColor Cyan

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env from template" -ForegroundColor Green
    Write-Host "   ⚠️  IMPORTANT: Edit .env file and add your API keys!" -ForegroundColor Yellow
} else {
    Write-Host "✅ .env file exists" -ForegroundColor Green
}

# Check for Gemini API key
try {
    $envContent = Get-Content ".env" -ErrorAction SilentlyContinue
    $geminiKey = $envContent | Where-Object { $_ -match "GEMINI_API_KEY=your_gemini_api_key_here" }
    if ($geminiKey) {
        Write-Host "⚠️  Gemini API key not configured" -ForegroundColor Yellow
        Write-Host "   Please get your API key from: https://makersuite.google.com/app/apikey" -ForegroundColor Yellow
        Write-Host "   Update GEMINI_API_KEY in your .env file" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Gemini API key configured" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Could not check Gemini API configuration" -ForegroundColor Yellow
}

# Test database connection
Write-Host ""
Write-Host "🔗 Testing database connection..." -ForegroundColor Cyan
try {
    $result = python -c "
try:
    from core.database import engine
    with engine.connect() as conn:
        result = conn.execute('SELECT 1')
        print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database connection successful" -ForegroundColor Green
    } else {
        Write-Host "❌ Database connection failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Database connection test failed" -ForegroundColor Red
    exit 1
}

# Test LLM configuration
Write-Host ""
Write-Host "🤖 Testing LLM configuration..." -ForegroundColor Cyan
try {
    $result = python -c "
import os
from services.llm_resume_extractor import LLMResumeExtractor

try:
    extractor = LLMResumeExtractor()
    print(f'llm configuration successful - Provider: {extractor.provider}')
except Exception as e:
    print(f'llm configuration issue: {e}')
" 2>$null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ LLM configuration successful" -ForegroundColor Green
    } else {
        Write-Host "⚠️  LLM configuration needs attention" -ForegroundColor Yellow
        Write-Host "   This is expected if API keys are not configured yet" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not test LLM configuration" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎯 Setup Summary:" -ForegroundColor Green
Write-Host "================" -ForegroundColor Green

# Check what's ready vs what needs configuration
$readyItems = @()
$todoItems = @()

# Database check
try {
    $result = python -c "
from core.database import engine
with engine.connect() as conn:
    conn.execute('SELECT 1')
    print('Database: Connected and ready')
" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $readyItems += "Database"
    } else {
        $todoItems += "Database setup"
    }
} catch {
    $todoItems += "Database setup"
}

# Dependencies check
try {
    $result = pip list 2>$null | Select-String "fastapi|sqlalchemy|google-generativeai"
    if ($result) {
        $readyItems += "Dependencies"
    } else {
        $todoItems += "Install dependencies"
    }
} catch {
    $todoItems += "Install dependencies"
}

# Environment file check
if (Test-Path ".env") {
    $readyItems += "Environment file"
} else {
    $todoItems += "Create .env file"
}

# Gemini API key check
try {
    $envContent = Get-Content ".env" -ErrorAction SilentlyContinue
    $hasGeminiKey = $envContent | Where-Object { $_ -notmatch "GEMINI_API_KEY=your_gemini_api_key_here" }
    if ($hasGeminiKey) {
        $readyItems += "Gemini API"
    } else {
        $todoItems += "Configure Gemini API key"
    }
} catch {
    $todoItems += "Configure Gemini API key"
}

Write-Host ""
Write-Host "📋 Setup Status:" -ForegroundColor Cyan
Write-Host "================" -ForegroundColor Cyan
Write-Host "✅ Ready ($($readyItems.Count) items):" -ForegroundColor Green
foreach ($item in $readyItems) {
    Write-Host "   • $item" -ForegroundColor Green
}

if ($todoItems.Count -gt 0) {
    Write-Host ""
    Write-Host "⚠️  Needs Attention ($($todoItems.Count) items):" -ForegroundColor Yellow
    foreach ($item in $todoItems) {
        Write-Host "   • $item" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Green
Write-Host "==============" -ForegroundColor Green

if ($todoItems.Count -eq 0) {
    Write-Host "🎉 You're all set! Run the application:" -ForegroundColor Green
    Write-Host "   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
    Write-Host ""
    Write-Host "   Visit: http://localhost:8000" -ForegroundColor Cyan
} else {
    Write-Host "1. Configure your API keys in .env file" -ForegroundColor White
    Write-Host "2. Run: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
    Write-Host "3. Visit: http://localhost:8000" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "📚 Additional Resources:" -ForegroundColor Green
Write-Host "=======================" -ForegroundColor Green
Write-Host "• Complete setup guide: README_LOCAL_SETUP.md" -ForegroundColor White
Write-Host "• API documentation: http://localhost:8000/docs (after starting)" -ForegroundColor White
Write-Host "• Troubleshooting: See README_LOCAL_SETUP.md" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Cyan
Write-Host "• Use SQLite for quick development (no database setup needed)" -ForegroundColor White
Write-Host "• PostgreSQL recommended for full feature compatibility" -ForegroundColor White
Write-Host "• Get Gemini API key from: https://makersuite.google.com/app/apikey" -ForegroundColor White
Write-Host ""
Write-Host "✅ Setup script completed!" -ForegroundColor Green
