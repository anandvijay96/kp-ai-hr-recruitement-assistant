#!/usr/bin/env python3
"""
Script to clear all candidate-related data from database for fresh start
"""
import sqlite3
import os

def clear_database():
    """Clear all candidate, resume, and related data"""
    db_path = "hr_recruitment.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🗑️  Clearing database...")
        
        # Delete in correct order (respecting foreign keys)
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
                print(f"⚠️  Could not clear {table}: {str(e)}")
        
        conn.commit()
        print("\n✅ Database cleared successfully!")
        print("\n📊 Summary:")
        print("- All candidates removed")
        print("- All resumes removed")
        print("- All skills, education, experience, certifications removed")
        print("\n🚀 Ready for fresh upload!")
        
    except Exception as e:
        print(f"❌ Error clearing database: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("⚠️  WARNING: This will delete ALL candidate data!")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() == 'yes':
        clear_database()
    else:
        print("❌ Operation cancelled")
