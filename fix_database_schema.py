"""
Fix database schema - Add missing columns and fix constraints
"""
import sqlite3
import os
from pathlib import Path

def fix_database(db_path):
    """Add missing columns and fix constraints in a database file"""
    if not os.path.exists(db_path):
        print(f"  Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n📁 Processing: {db_path}")
        
        fixed_something = False
        
        # Fix jobs table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(jobs)")
            columns = [row[1] for row in cursor.fetchall()]
            
            columns_to_add = []
            if 'archived_at' not in columns:
                columns_to_add.append(('archived_at', 'TIMESTAMP'))
            if 'view_count' not in columns:
                columns_to_add.append(('view_count', 'INTEGER DEFAULT 0'))
            if 'application_deadline' not in columns:
                columns_to_add.append(('application_deadline', 'TIMESTAMP'))
            
            for col_name, col_type in columns_to_add:
                try:
                    cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")
                    print(f"  ✓ Added jobs.{col_name}")
                    fixed_something = True
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        raise
        
        # Fix resumes table - Make uploaded_by nullable
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='resumes'")
        if cursor.fetchone():
            print("  🔧 Checking resumes.uploaded_by constraint...")
            
            # SQLite doesn't support ALTER COLUMN, so we need to check the schema
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='resumes'")
            create_sql = cursor.fetchone()[0]
            
            # Check if uploaded_by has NOT NULL constraint
            if 'uploaded_by' in create_sql and 'NOT NULL' in create_sql:
                # Need to recreate table without NOT NULL on uploaded_by
                print("  ⚠️  uploaded_by has NOT NULL constraint - needs manual fix")
                print("  💡 Solution: Delete hr_recruitment.db and restart app to recreate with correct schema")
                print("  💡 Or run: python -c \"import os; os.remove('hr_recruitment.db')\" then restart")
            else:
                print("  ✅ uploaded_by is already nullable")
        
        if fixed_something:
            conn.commit()
            print("  ✅ Schema updated successfully")
        else:
            print("  ✅ All columns already present")
        
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
