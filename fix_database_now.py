#!/usr/bin/env python3
"""
One-time database fix script
Run this to add missing columns to the users table
"""
import sqlite3
import os

def fix_database():
    db_path = "hr_recruitment.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current columns
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        print("Current columns:", columns)
        print()
        
        # Add missing columns
        columns_to_add = {
            'status': "VARCHAR(50) DEFAULT 'active'",
            'deactivation_reason': "TEXT",
            'last_activity_at': "TIMESTAMP",
            'locked_until': "TIMESTAMP"
        }
        
        added = []
        for column_name, column_type in columns_to_add.items():
            if column_name not in columns:
                try:
                    sql = f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"
                    print(f"Adding column: {column_name}...")
                    cursor.execute(sql)
                    added.append(column_name)
                    print(f"✅ Added: {column_name}")
                except sqlite3.OperationalError as e:
                    if 'duplicate column' in str(e).lower():
                        print(f"⚠️  Column {column_name} already exists")
                    else:
                        print(f"❌ Error adding {column_name}: {e}")
                        return False
            else:
                print(f"✓ Column {column_name} already exists")
        
        conn.commit()
        conn.close()
        
        print()
        if added:
            print(f"✅ SUCCESS! Added {len(added)} columns: {', '.join(added)}")
        else:
            print("✅ All columns already exist!")
        
        print()
        print("Database is now ready. You can:")
        print("  1. Start the server: python -m uvicorn main:app --reload")
        print("  2. Go to: http://localhost:8000/users")
        print("  3. Create users without errors")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  Database Fix Script")
    print("=" * 60)
    print()
    
    success = fix_database()
    
    print()
    print("=" * 60)
    exit(0 if success else 1)
