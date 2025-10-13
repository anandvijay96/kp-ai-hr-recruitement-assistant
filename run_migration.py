"""
Simple script to run the jobs management migration
Run with: uv run python run_migration.py
"""
import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from migrations import migrations_008_create_jobs_management_tables

if __name__ == "__main__":
    print("=" * 60)
    print("Running Jobs Management Migration (008)")
    print("=" * 60)
    
    try:
        asyncio.run(migrations_008_create_jobs_management_tables.upgrade())
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Migration failed: {str(e)}")
        print("=" * 60)
        sys.exit(1)
