"""
Script to add professional_summary column to candidates table
"""
import sqlite3

# Connect to database
conn = sqlite3.connect('hr_recruitment.db')
cursor = conn.cursor()

try:
    # Add column
    cursor.execute("ALTER TABLE candidates ADD COLUMN professional_summary TEXT")
    conn.commit()
    print("✅ Successfully added professional_summary column to candidates table")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("⚠️  Column already exists")
    else:
        print(f"❌ Error: {e}")
finally:
    conn.close()
