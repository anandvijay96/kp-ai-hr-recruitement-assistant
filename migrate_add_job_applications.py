#!/usr/bin/env python3
"""
Migration script to add job_applications table
"""
import sqlite3
import os

def migrate():
    """Add job_applications table"""
    db_path = "hr_recruitment.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='job_applications'
        """)
        exists = cursor.fetchone()
        
        if not exists:
            print("Creating job_applications table...")
            cursor.execute("""
                CREATE TABLE job_applications (
                    id VARCHAR(36) PRIMARY KEY,
                    job_id VARCHAR(36) NOT NULL,
                    candidate_id VARCHAR(36) NOT NULL,
                    status VARCHAR(50) DEFAULT 'applied',
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
                    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX idx_job_applications_job_id ON job_applications(job_id)")
            cursor.execute("CREATE INDEX idx_job_applications_candidate_id ON job_applications(candidate_id)")
            cursor.execute("CREATE INDEX idx_job_applications_status ON job_applications(status)")
            cursor.execute("CREATE INDEX idx_job_applications_applied_at ON job_applications(applied_at)")
            
            # Create unique constraint on job_id + candidate_id
            cursor.execute("""
                CREATE UNIQUE INDEX idx_job_applications_unique 
                ON job_applications(job_id, candidate_id)
            """)
            
            print("✅ Created job_applications table with indexes")
        else:
            print("✅ job_applications table already exists")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting job_applications table migration...")
    print("=" * 60)
    migrate()
