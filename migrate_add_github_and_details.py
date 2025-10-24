#!/usr/bin/env python3
"""
Migration script to add:
1. github_url column to candidates table
2. authenticity_details and jd_match_details columns to resumes table
"""
import sqlite3
import os

def migrate():
    """Add new columns to candidates and resumes tables"""
    db_path = "hr_recruitment.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # ===== CANDIDATES TABLE =====
        print("\n📋 Migrating candidates table...")
        cursor.execute("PRAGMA table_info(candidates)")
        candidate_columns = [row[1] for row in cursor.fetchall()]
        
        # Add github_url if not exists
        if 'github_url' not in candidate_columns:
            print("Adding github_url column...")
            cursor.execute("ALTER TABLE candidates ADD COLUMN github_url VARCHAR(500)")
            print("✅ Added github_url column")
        else:
            print("✅ github_url column already exists")
        
        # ===== RESUMES TABLE =====
        print("\n📋 Migrating resumes table...")
        cursor.execute("PRAGMA table_info(resumes)")
        resume_columns = [row[1] for row in cursor.fetchall()]
        
        # Add authenticity_details if not exists
        if 'authenticity_details' not in resume_columns:
            print("Adding authenticity_details column...")
            cursor.execute("ALTER TABLE resumes ADD COLUMN authenticity_details JSON")
            print("✅ Added authenticity_details column")
        else:
            print("✅ authenticity_details column already exists")
        
        # Add jd_match_details if not exists
        if 'jd_match_details' not in resume_columns:
            print("Adding jd_match_details column...")
            cursor.execute("ALTER TABLE resumes ADD COLUMN jd_match_details JSON")
            print("✅ Added jd_match_details column")
        else:
            print("✅ jd_match_details column already exists")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\n📊 New columns added:")
        print("   • candidates.github_url (VARCHAR 500)")
        print("   • resumes.authenticity_details (JSON)")
        print("   • resumes.jd_match_details (JSON)")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting database migration...")
    print("=" * 60)
    migrate()
