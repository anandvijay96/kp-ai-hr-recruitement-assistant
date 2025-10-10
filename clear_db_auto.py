#!/usr/bin/env python3
"""Auto-clear database without confirmation"""
import sqlite3
import os

db_path = "hr_recruitment.db"

if not os.path.exists(db_path):
    print(f"❌ Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print("🗑️  Clearing database...")
    
    tables_to_clear = [
        "candidate_skills",
        "certifications", 
        "work_experience",
        "education",
        "resumes",
        "candidates"
    ]
    
    for table in tables_to_clear:
        try:
            cursor.execute(f"DELETE FROM {table}")
            count = cursor.rowcount
            print(f"✅ Cleared {count} records from {table}")
        except Exception as e:
            print(f"⚠️  {table}: {str(e)}")
    
    conn.commit()
    print("\n✅ Database cleared successfully!")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    conn.rollback()
finally:
    conn.close()
