"""
Migration: Add soft delete columns to candidates table (PostgreSQL)
Date: 2025-10-21
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from core.database import get_engine

async def run_migration():
    """Add soft delete columns to candidates table"""
    
    engine = get_engine()
    
    try:
        print("🔄 Starting migration: Add soft delete columns to candidates table")
        
        async with engine.begin() as conn:
            # Check if table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'candidates'
                )
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print("❌ Error: candidates table does not exist!")
                print("💡 Please run database initialization first:")
                print("   python init_database.py")
                return False
            
            # Check existing columns
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'candidates'
            """))
            existing_columns = [row[0] for row in result.fetchall()]
            
            print(f"📋 Found {len(existing_columns)} existing columns in candidates table")
            
            # Columns to add
            columns_to_add = {
                'is_deleted': 'BOOLEAN DEFAULT FALSE NOT NULL',
                'deleted_at': 'TIMESTAMP',
                'deleted_by': 'VARCHAR(255)',
                'deletion_reason': 'TEXT'
            }
            
            # Add columns if they don't exist
            for column_name, column_def in columns_to_add.items():
                if column_name not in existing_columns:
                    print(f"  ➕ Adding column: {column_name}")
                    await conn.execute(text(f"""
                        ALTER TABLE candidates 
                        ADD COLUMN {column_name} {column_def}
                    """))
                else:
                    print(f"  ✓ Column already exists: {column_name}")
            
            # Create index on is_deleted for faster queries
            try:
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_candidates_is_deleted 
                    ON candidates(is_deleted)
                """))
                print("  ✓ Created index on is_deleted")
            except Exception as e:
                print(f"  ⚠️ Index creation skipped: {e}")
            
            print("✅ Migration completed successfully!")
            
            # Verify
            result = await conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'candidates' 
                AND column_name LIKE '%delete%'
                ORDER BY ordinal_position
            """))
            delete_cols = result.fetchall()
            
            print(f"\n📊 Verification: Found {len(delete_cols)} soft delete columns:")
            for col_name, col_type in delete_cols:
                print(f"  - {col_name}: {col_type}")
            
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_migration())
    sys.exit(0 if success else 1)
