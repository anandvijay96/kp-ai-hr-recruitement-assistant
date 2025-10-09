#!/usr/bin/env python3
"""Test script to verify all imports work correctly"""

print("Testing imports...")

try:
    print("1. Testing core.config...")
    from core.config import settings
    print(f"   ✅ Database URL: {settings.database_url}")
    
    print("\n2. Testing aiosqlite module...")
    import aiosqlite
    print(f"   ✅ aiosqlite version: {aiosqlite.__version__ if hasattr(aiosqlite, '__version__') else 'installed'}")
    
    print("\n3. Testing core.database...")
    from core.database import get_engine, Base
    print("   ✅ Database module imported")
    
    print("\n4. Testing main.py...")
    import main
    print("   ✅ main.py imported successfully!")
    
    print("\n" + "="*50)
    print("🎉 ALL IMPORTS SUCCESSFUL!")
    print("="*50)
    print("\nYou can now start the server with:")
    print("  uvicorn main:app --reload --port 8000")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "="*50)
    print("Fix needed - see error above")
    print("="*50)
