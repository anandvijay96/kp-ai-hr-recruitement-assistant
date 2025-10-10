#!/usr/bin/env python3
"""
Simple migration script to add authenticity_score and jd_match_score columns to resumes table
"""
import sqlite3
import os

def migrate():
    """Add score columns to resumes table"""
    db_path = "hr_recruitment.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get existing columns
        cursor.execute("PRAGMA table_info(resumes)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add authenticity_score if not exists
        if 'authenticity_score' not in columns:
            print("Adding authenticity_score column...")
            cursor.execute("ALTER TABLE resumes ADD COLUMN authenticity_score INTEGER")
            print("✅ Added authenticity_score column")
        else:
            print("✅ authenticity_score column already exists")
        
        # Add jd_match_score if not exists
        if 'jd_match_score' not in columns:
            print("Adding jd_match_score column...")
            cursor.execute("ALTER TABLE resumes ADD COLUMN jd_match_score INTEGER")
            print("✅ Added jd_match_score column")
        else:
            print("✅ jd_match_score column already exists")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting migration...")
    migrate()
