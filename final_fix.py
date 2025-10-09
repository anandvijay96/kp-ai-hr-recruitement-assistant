#!/usr/bin/env python3
"""Final database fix - Run this once to fix everything"""
import sqlite3
import os
import sys

def main():
    print("=" * 70)
    print("  FINAL DATABASE FIX")
    print("=" * 70)
    print()
    
    db_path = "hr_recruitment.db"
    
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return 1
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current columns
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        print(f"Found {len(existing_columns)} existing columns")
        print()
        
        # Columns to add
        new_columns = {
            'status': "VARCHAR(50) DEFAULT 'active'",
            'deactivation_reason': "TEXT",
            'last_activity_at': "TIMESTAMP",
            'locked_until': "TIMESTAMP"
        }
        
        added = 0
        for col_name, col_def in new_columns.items():
            if col_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"
                    print(f"Adding: {col_name}...")
                    cursor.execute(sql)
                    added += 1
                    print(f"  ✅ Added {col_name}")
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    return 1
            else:
                print(f"  ✓ {col_name} already exists")
        
        conn.commit()
        
        # Verify
        cursor.execute("PRAGMA table_info(users)")
        final_columns = {row[1] for row in cursor.fetchall()}
        
        print()
        print(f"Total columns now: {len(final_columns)}")
        
        # Check for admin user
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'admin@example.com'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            print()
            print("⚠️  No admin user found")
            print("   Admin will be created automatically when you create your first user")
        else:
            print()
            print(f"✅ Admin user exists")
        
        conn.close()
        
        print()
        print("=" * 70)
        if added > 0:
            print(f"✅ SUCCESS! Added {added} columns")
        else:
            print("✅ Database already up to date")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Restart server: python -m uvicorn main:app --reload")
        print("  2. Go to: http://localhost:8000/users")
        print("  3. Click 'Create User' and fill in details")
        print("  4. User will be created successfully!")
        print()
        
        return 0
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
