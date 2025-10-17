"""
Migration: Add soft delete columns to candidates table
Date: 2025-10-18
"""
import sqlite3
from datetime import datetime

def run_migration():
    """Add soft delete columns to candidates table"""
    
    db_path = './hr_assistant.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔄 Starting migration: Add soft delete columns to candidates table")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(candidates)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        columns_to_add = {
            'is_deleted': 'INTEGER DEFAULT 0 NOT NULL',
            'deleted_at': 'DATETIME',
            'deleted_by': 'VARCHAR(255)',
            'deletion_reason': 'TEXT'
        }
        
        for column_name, column_def in columns_to_add.items():
            if column_name not in existing_columns:
                print(f"  ➕ Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE candidates ADD COLUMN {column_name} {column_def}")
            else:
                print(f"  ✓ Column already exists: {column_name}")
        
        # Create index on is_deleted for faster queries
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_is_deleted ON candidates(is_deleted)")
            print("  ✓ Created index on is_deleted")
        except Exception as e:
            print(f"  ⚠️ Index creation skipped: {e}")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
        # Verify
        cursor.execute("PRAGMA table_info(candidates)")
        columns = cursor.fetchall()
        delete_cols = [c for c in columns if 'delete' in c[1].lower()]
        
        print(f"\n📊 Verification: Found {len(delete_cols)} soft delete columns:")
        for col in delete_cols:
            print(f"  - {col[1]}: {col[2]}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
