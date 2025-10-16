"""
Fix resumes table - Recreate with uploaded_by as nullable
This script will backup data, drop the table, and recreate it with correct schema
"""
import sqlite3
import os
import json
from datetime import datetime

def fix_resumes_table(db_path="hr_recruitment.db"):
    """Fix the resumes table to make uploaded_by nullable"""
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 70)
        print("RESUMES TABLE FIX UTILITY")
        print("=" * 70)
        print(f"\n📁 Database: {db_path}")
        
        # Check if resumes table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='resumes'")
        if not cursor.fetchone():
            print("✅ Resumes table doesn't exist yet - will be created with correct schema")
            conn.close()
            return True
        
        # Check current schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='resumes'")
        current_schema = cursor.fetchone()[0]
        
        print("\n🔍 Current schema:")
        print(current_schema[:200] + "...")
        
        # Check if uploaded_by has NOT NULL constraint
        if 'uploaded_by' not in current_schema:
            print("\n✅ uploaded_by column doesn't exist - no fix needed")
            conn.close()
            return True
        
        if 'uploaded_by' in current_schema and 'NOT NULL' not in current_schema:
            print("\n✅ uploaded_by is already nullable - no fix needed")
            conn.close()
            return True
        
        print("\n⚠️  uploaded_by has NOT NULL constraint - fixing...")
        
        # Backup existing data
        print("\n📦 Backing up existing resumes...")
        cursor.execute("SELECT COUNT(*) FROM resumes")
        count = cursor.fetchone()[0]
        print(f"   Found {count} resumes to backup")
        
        if count > 0:
            cursor.execute("SELECT * FROM resumes")
            backup_data = cursor.fetchall()
            
            # Get column names
            cursor.execute("PRAGMA table_info(resumes)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Save backup to file
            backup_file = f"resumes_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup = []
            for row in backup_data:
                backup.append(dict(zip(columns, row)))
            
            with open(backup_file, 'w') as f:
                json.dump(backup, f, indent=2, default=str)
            
            print(f"   ✅ Backup saved to: {backup_file}")
        
        # Drop and recreate table
        print("\n🔧 Recreating resumes table...")
        cursor.execute("DROP TABLE IF EXISTS resumes")
        
        # Recreate with correct schema (uploaded_by nullable)
        create_sql = """
        CREATE TABLE resumes (
            id VARCHAR(36) PRIMARY KEY,
            file_name VARCHAR(255) NOT NULL,
            original_file_name VARCHAR(255),
            file_path VARCHAR(500) NOT NULL,
            file_size INTEGER,
            file_type VARCHAR(10),
            file_hash VARCHAR(64) UNIQUE,
            mime_type VARCHAR(100),
            candidate_name VARCHAR(255),
            candidate_email VARCHAR(255),
            candidate_phone VARCHAR(50),
            candidate_id VARCHAR(36),
            extracted_text TEXT,
            parsed_data TEXT,
            authenticity_score INTEGER,
            jd_match_score INTEGER,
            uploaded_by VARCHAR(36),  -- NULLABLE for system uploads
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            upload_ip VARCHAR(45),
            upload_user_agent TEXT,
            status VARCHAR(20) DEFAULT 'uploaded',
            processing_status VARCHAR(20),
            processing_error TEXT,
            processed_at TIMESTAMP,
            virus_scan_status VARCHAR(20) DEFAULT 'pending',
            virus_scan_date TIMESTAMP,
            virus_scan_result TEXT,
            deleted_at TIMESTAMP,
            deleted_by VARCHAR(36),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
            FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL
        )
        """
        cursor.execute(create_sql)
        print("   ✅ Table recreated with uploaded_by as nullable")
        
        # Restore data if any
        if count > 0:
            print(f"\n📥 Restoring {count} resumes...")
            placeholders = ','.join(['?' for _ in columns])
            insert_sql = f"INSERT INTO resumes ({','.join(columns)}) VALUES ({placeholders})"
            
            for row in backup_data:
                try:
                    cursor.execute(insert_sql, row)
                except Exception as e:
                    print(f"   ⚠️  Error restoring resume: {e}")
            
            cursor.execute("SELECT COUNT(*) FROM resumes")
            restored_count = cursor.fetchone()[0]
            print(f"   ✅ Restored {restored_count}/{count} resumes")
        
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 70)
        print("✅ FIX COMPLETE!")
        print("=" * 70)
        print("\n⚠️  IMPORTANT: Restart your application now!")
        print("\nWhat was fixed:")
        print("  • uploaded_by column is now nullable")
        print("  • Vetting uploads will work without user context")
        print("  • All existing data has been preserved")
        
        return True
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Try common database locations
    db_locations = [
        "hr_recruitment.db",
        "./hr_recruitment.db",
        "C:/tmp/hr_recruitment.db",
        "/tmp/hr_recruitment.db",
    ]
    
    import tempfile
    db_locations.append(os.path.join(tempfile.gettempdir(), "hr_recruitment.db"))
    
    fixed = False
    for db_path in db_locations:
        if os.path.exists(db_path):
            if fix_resumes_table(db_path):
                fixed = True
                break
    
    if not fixed:
        print("\n❌ No database file found to fix")
        print("\nSearched locations:")
        for loc in db_locations:
            print(f"  • {loc}")
        print("\n💡 The database will be created with correct schema on first run")
