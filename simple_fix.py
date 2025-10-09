"""Simple database fix - no dependencies"""
import sqlite3
import os

db_path = "hr_recruitment.db"

if not os.path.exists(db_path):
    print(f"❌ Database not found at {db_path}")
    print("Make sure you're running this from the project root directory")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Fixing database schema...")
    
    # Try to add each column
    columns_added = []
    
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN archived_at TIMESTAMP")
        columns_added.append("archived_at")
        print("  ✓ Added archived_at")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("  ✓ archived_at already exists")
        else:
            print(f"  ⚠️  archived_at: {e}")
    
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN view_count INTEGER DEFAULT 0")
        columns_added.append("view_count")
        print("  ✓ Added view_count")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("  ✓ view_count already exists")
        else:
            print(f"  ⚠️  view_count: {e}")
    
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN application_deadline TIMESTAMP")
        columns_added.append("application_deadline")
        print("  ✓ Added application_deadline")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("  ✓ application_deadline already exists")
        else:
            print(f"  ⚠️  application_deadline: {e}")
    
    conn.commit()
    
    # Verify
    cursor.execute("PRAGMA table_info(jobs)")
    all_columns = [row[1] for row in cursor.fetchall()]
    
    required = ['archived_at', 'view_count', 'application_deadline']
    all_present = all(col in all_columns for col in required)
    
    conn.close()
    
    print("\n" + "=" * 60)
    if all_present:
        print("✅ DATABASE FIXED SUCCESSFULLY!")
        print("\n⚠️  IMPORTANT: Restart your application now!")
        print("   Press Ctrl+C in the app terminal, then run:")
        print("   uvicorn main:app --reload")
    else:
        missing = [col for col in required if col not in all_columns]
        print(f"❌ Still missing columns: {missing}")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
