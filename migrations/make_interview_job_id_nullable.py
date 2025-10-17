"""
Migration: Make interviews.job_id nullable
============================================
Allows scheduling interviews without job assignment.

Run this script to update existing database.
"""
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def migrate():
    """Make job_id nullable in interviews table"""
    db_path = "hr_recruitment.db"
    
    print(f"🔄 Migrating database: {db_path}")
    print("Making interviews.job_id nullable...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # SQLite doesn't support ALTER COLUMN directly
        # We need to recreate the table
        
        # 1. Create new table with nullable job_id
        print("  1. Creating new interviews table...")
        cursor.execute("""
            CREATE TABLE interviews_new (
                id TEXT PRIMARY KEY,
                candidate_id TEXT NOT NULL,
                job_id TEXT,  -- Now nullable
                scheduled_by TEXT NOT NULL,
                interviewer_ids TEXT,
                scheduled_datetime TIMESTAMP NOT NULL,
                duration_minutes INTEGER DEFAULT 60,
                timezone TEXT DEFAULT 'UTC',
                interview_type TEXT NOT NULL,
                interview_round INTEGER DEFAULT 1,
                location TEXT,
                meeting_link TEXT,
                meeting_id TEXT,
                meeting_password TEXT,
                status TEXT DEFAULT 'scheduled',
                reminder_sent INTEGER DEFAULT 0,
                confirmation_sent INTEGER DEFAULT 0,
                notes TEXT,
                feedback TEXT,
                rating INTEGER,
                recommendation TEXT,
                original_datetime TIMESTAMP,
                reschedule_reason TEXT,
                rescheduled_by TEXT,
                reschedule_count INTEGER DEFAULT 0,
                cancelled_at TIMESTAMP,
                cancelled_by TEXT,
                cancellation_reason TEXT,
                completed_at TIMESTAMP,
                completed_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
                FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
                FOREIGN KEY (scheduled_by) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (rescheduled_by) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (cancelled_by) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (completed_by) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        
        # 2. Copy data from old table (if it exists and has data)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interviews'")
        if cursor.fetchone():
            print("  2. Copying existing data...")
            cursor.execute("""
                INSERT INTO interviews_new 
                SELECT * FROM interviews
            """)
            
            # 3. Drop old table
            print("  3. Dropping old table...")
            cursor.execute("DROP TABLE interviews")
        else:
            print("  2. No existing interviews table found (fresh install)")
        
        # 4. Rename new table
        print("  4. Renaming new table...")
        cursor.execute("ALTER TABLE interviews_new RENAME TO interviews")
        
        # 5. Create indexes
        print("  5. Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_interviews_candidate_id ON interviews(candidate_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_interviews_job_id ON interviews(job_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_interviews_scheduled_by ON interviews(scheduled_by)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_interviews_scheduled_datetime ON interviews(scheduled_datetime)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_interviews_interview_type ON interviews(interview_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_interviews_status ON interviews(status)")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        print("   - job_id is now nullable")
        print("   - Can schedule interviews without job assignment")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
