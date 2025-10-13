"""
Fix database schema - Add missing columns to ALL database files
"""
import sqlite3
import os
from pathlib import Path

def fix_database(db_path):
    """Add missing columns to a database file"""
    if not os.path.exists(db_path):
        print(f"  Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n📁 Processing: {db_path}")
        
        # Check if jobs table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
        if not cursor.fetchone():
            print("  ⚠️  Jobs table doesn't exist - skipping")
            conn.close()
            return False
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(jobs)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add missing columns
        columns_to_add = []
        
        if 'archived_at' not in columns:
            columns_to_add.append(('archived_at', 'TIMESTAMP'))
        
        if 'view_count' not in columns:
            columns_to_add.append(('view_count', 'INTEGER DEFAULT 0'))
        
        if 'application_deadline' not in columns:
            columns_to_add.append(('application_deadline', 'TIMESTAMP'))
        
        if not columns_to_add:
            print("  ✅ All columns already present")
        else:
            for col_name, col_type in columns_to_add:
                try:
                    cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")
                    print(f"  ✓ Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"  ⚠️  Column {col_name} already exists")
                    else:
                        raise
            
            conn.commit()
            print("  ✅ Schema updated successfully")
        
        conn.close()
        return True
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


# List of possible database locations
db_locations = [
    "hr_recruitment.db",  # Project root
    "./hr_recruitment.db",
    "C:/tmp/hr_recruitment.db",  # Windows style /tmp
    "/tmp/hr_recruitment.db",  # Unix style /tmp
]

# Also check Windows temp directories
import tempfile
temp_dir = tempfile.gettempdir()
db_locations.append(os.path.join(temp_dir, "hr_recruitment.db"))

print("=" * 70)
print("DATABASE SCHEMA FIX UTILITY")
print("=" * 70)
print("\nSearching for database files...")

fixed_count = 0
for db_path in db_locations:
    if fix_database(db_path):
        fixed_count += 1

print("\n" + "=" * 70)
if fixed_count > 0:
    print(f"✅ Fixed {fixed_count} database file(s)")
    print("\n⚠️  IMPORTANT: Restart your application for changes to take effect!")
else:
    print("❌ No database files were fixed")
    print("\nTip: The database might be created at runtime.")
    print("     Try running the app once, then run this script again.")
print("=" * 70)
