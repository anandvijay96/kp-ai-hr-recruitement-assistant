#!/usr/bin/env python3
"""
AI HR Assistant - Setup Verification Script

This script verifies that all components are properly configured and working.
Run this after completing the setup process.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def check_database():
    """Check database connection and schema."""
    print("🔗 Checking database connection...")

    try:
        from core.database import engine, Base
        from core.models import User, Candidate, Resume  # Import some models

        # Test connection
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("   ✅ Database connected successfully")
        return True

    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

async def check_llm_configuration():
    """Check LLM API configuration."""
    print("🤖 Checking LLM configuration...")

    try:
        from services.llm_resume_extractor import LLMResumeExtractor

        # Try to initialize extractor
        extractor = LLMResumeExtractor()

        # Check if API keys are configured
        gemini_configured = os.getenv('GEMINI_API_KEY') not in [None, '', 'your_gemini_api_key_here']
        openai_configured = os.getenv('OPENAI_API_KEY') not in [None, '', 'your_openai_api_key_here']

        if gemini_configured:
            print(f"   ✅ Gemini API configured (Provider: {extractor.provider})")
        elif openai_configured:
            print(f"   ✅ OpenAI API configured (Provider: {extractor.provider})")
        else:
            print("   ⚠️  No LLM API keys configured")
            print("      Gemini: Get key from https://makersuite.google.com/app/apikey")
            print("      OpenAI: Get key from https://platform.openai.com/api-keys")

        return gemini_configured or openai_configured

    except Exception as e:
        print(f"   ❌ LLM configuration check failed: {e}")
        return False

def check_file_uploads():
    """Check if upload directories exist and are writable."""
    print("📁 Checking file upload setup...")

    required_dirs = [
        'uploads',
        'uploads/resumes',
        'uploads/temp',
        'logs',
        'results',
        'temp/vetting_sessions'
    ]

    all_good = True

    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            if os.access(dir_path, os.W_OK):
                print(f"   ✅ {dir_path} (writable)")
            else:
                print(f"   ❌ {dir_path} (not writable)")
                all_good = False
        else:
            print(f"   ⚠️  {dir_path} (missing - will be created)")
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"   ✅ {dir_path} (created)")
            except Exception as e:
                print(f"   ❌ {dir_path} (cannot create: {e})")
                all_good = False

    return all_good

def check_dependencies():
    """Check if all required Python packages are installed."""
    print("📦 Checking Python dependencies...")

    required_packages = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'alembic',
        'google-generativeai', 'python-multipart', 'aiofiles'
    ]

    missing = []

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (missing)")
            missing.append(package)

    if missing:
        print(f"\n   💡 Install missing packages: pip install {' '.join(missing)}")
        return False

    return True

def check_environment_file():
    """Check if .env file exists and has required variables."""
    print("🔐 Checking environment configuration...")

    if not os.path.exists('.env'):
        print("   ❌ .env file missing")
        print("   💡 Copy .env.example to .env and configure your API keys")
        return False

    # Check for critical environment variables
    critical_vars = ['DATABASE_URL', 'SECRET_KEY']
    missing_vars = []

    for var in critical_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"   ❌ Missing critical environment variables: {', '.join(missing_vars)}")
        return False

    print("   ✅ Environment file exists and configured")
    return True

async def check_api_endpoints():
    """Test basic API endpoints."""
    print("🌐 Testing API endpoints...")

    try:
        import httpx

        async with httpx.AsyncClient() as client:
            # Test health endpoint
            response = await client.get("http://localhost:8000/api/health", timeout=5.0)

            if response.status_code == 200:
                print("   ✅ Health endpoint responding")
                return True
            else:
                print(f"   ❌ Health endpoint returned {response.status_code}")
                return False

    except Exception as e:
        print(f"   ❌ API endpoint test failed: {e}")
        print("   💡 Make sure the application is running on port 8000")
        return False

async def main():
    """Run all verification checks."""
    print("🚀 AI HR Assistant - Setup Verification")
    print("=" * 50)

    checks = [
        ("Dependencies", check_dependencies),
        ("Environment File", check_environment_file),
        ("Database", check_database),
        ("LLM Configuration", check_llm_configuration),
        ("File Uploads", check_file_uploads),
        ("API Endpoints", check_api_endpoints),
    ]

    results = []

    for check_name, check_func in checks:
        if asyncio.iscoroutinefunction(check_func):
            result = await check_func()
        else:
            result = check_func()
        results.append((check_name, result))

    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:<20} {status}")

    print(f"\n🎯 Overall: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 CONGRATULATIONS!")
        print("✅ Your AI HR Assistant is properly configured!")
        print("\n🚀 Next steps:")
        print("   1. Start the application: python -m uvicorn main:app --reload")
        print("   2. Visit: http://localhost:8000")
        print("   3. Upload a resume to test the system")
        print("   4. Check API docs: http://localhost:8000/docs")
    else:
        print(f"\n⚠️  {total - passed} issues need attention.")
        print("   Please fix the failed checks and run this script again.")
        print("   See README_LOCAL_SETUP.md for detailed setup instructions.")

    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
