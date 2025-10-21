"""
Migration: Fix user_activity_log table - add missing columns
Date: 2025-10-21
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from core.database import get_engine

async def run_migration():
    """Add missing columns to user_activity_log table"""
    
    engine = get_engine()
    
    try:
        print("🔄 Starting migration: Fix user_activity_log table")
        
        async with engine.begin() as conn:
            # Check if table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'user_activity_log'
                )
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print("❌ Error: user_activity_log table does not exist!")
                return False
            
            # Check existing columns
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'user_activity_log'
            """))
            existing_columns = [row[0] for row in result.fetchall()]
            
            print(f"📋 Found {len(existing_columns)} existing columns")
            
            # Columns that should exist
            required_columns = {
                'entity_type': 'VARCHAR(50)',
                'entity_id': 'VARCHAR(36)',
                'request_metadata': 'JSON',
                'request_method': 'VARCHAR(10)',
                'request_path': 'VARCHAR(500)',
                'duration_ms': 'INTEGER'
            }
            
            # Add missing columns
            for column_name, column_def in required_columns.items():
                if column_name not in existing_columns:
                    print(f"  ➕ Adding column: {column_name}")
                    await conn.execute(text(f"""
                        ALTER TABLE user_activity_log 
                        ADD COLUMN {column_name} {column_def}
                    """))
                else:
                    print(f"  ✓ Column already exists: {column_name}")
            
            # Create indexes
            try:
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_user_activity_log_entity_type 
                    ON user_activity_log(entity_type)
                """))
                print("  ✓ Created index on entity_type")
                
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_user_activity_log_entity_id 
                    ON user_activity_log(entity_id)
                """))
                print("  ✓ Created index on entity_id")
            except Exception as e:
                print(f"  ⚠️ Index creation skipped: {e}")
            
            print("✅ Migration completed successfully!")
            
            # Verify
            result = await conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'user_activity_log'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            print(f"\n📊 Verification: user_activity_log now has {len(columns)} columns")
            
            # Check for required columns
            col_names = [col[0] for col in columns]
            missing = [c for c in required_columns.keys() if c not in col_names]
            
            if missing:
                print(f"❌ Still missing: {missing}")
                return False
            else:
                print("✅ All required columns present!")
                return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_migration())
    sys.exit(0 if success else 1)
