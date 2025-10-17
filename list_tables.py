"""List all tables in database"""
import sqlite3

conn = sqlite3.connect('hr_recruitment.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("📋 Tables in hr_recruitment.db:\n")
for table in tables:
    print(f"  - {table[0]}")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    count = cursor.fetchone()[0]
    print(f"    Rows: {count}")

conn.close()
