"""
Migration: Create user_activity_log table
==========================================
Creates the activity logging table for tracking user actions.

Run this script to create the table in existing database.
"""
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def migrate():
    """Create user_activity_log table"""
    db_path = "hr_recruitment.db"
    
    print(f"🔄 Migrating database: {db_path}")
    print("Creating user_activity_log table...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_activity_log'")
        if cursor.fetchone():
            print("  ⚠️  Table already exists, skipping creation")
            conn.close()
            return
        
        # Create user_activity_log table
        print("  1. Creating user_activity_log table...")
        cursor.execute("""
            CREATE TABLE user_activity_log (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                entity_type TEXT,
                entity_id TEXT,
                metadata TEXT,
                ip_address TEXT,
                user_agent TEXT,
                request_method TEXT,
                request_path TEXT,
                duration_ms INTEGER,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for performance
        print("  2. Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_activity_log_user_id ON user_activity_log(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_activity_log_action_type ON user_activity_log(action_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_activity_log_entity_type ON user_activity_log(entity_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_activity_log_created_at ON user_activity_log(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_activity_log_status ON user_activity_log(status)")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        print("   - user_activity_log table created")
        print("   - Indexes created for performance")
        print("   - Activity tracking is now enabled")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
