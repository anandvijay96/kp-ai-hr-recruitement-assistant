"""Check table schema"""
import sqlite3

conn = sqlite3.connect('hr_recruitment.db')
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(user_activity_log)")
columns = cursor.fetchall()

print("📋 user_activity_log columns:\n")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()
