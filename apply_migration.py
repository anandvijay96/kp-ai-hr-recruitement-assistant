"""
Apply Jobs Management Migration
Run with: uv run python apply_migration.py
"""
import asyncio
import sqlite3
import os

async def apply_migration():
    """Apply the SQL migration to the database"""
    
    # Find the database file
    db_path = "hr_recruitment.db"
    if not os.path.exists(db_path):
        # Try alternative name
        db_path = "database.db"
        if not os.path.exists(db_path):
            print(f"❌ Database file not found: {db_path}")
            return False
    
    # Read the SQL migration file
    sql_file = "migrations/008_create_jobs_management_tables.sql"
    if not os.path.exists(sql_file):
        print(f"❌ Migration file not found: {sql_file}")
        return False
    
    with open(sql_file, 'r') as f:
        sql_script = f.read()
    
    # Connect to database and execute
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 60)
        print("Applying Jobs Management Migration (008)")
        print("=" * 60)
        
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql_script.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for i, statement in enumerate(statements, 1):
            try:
                # Skip comments
                if statement.startswith('--'):
                    continue
                    
                cursor.execute(statement)
                
                # Print progress for CREATE TABLE and ALTER TABLE statements
                if 'CREATE TABLE' in statement.upper():
                    table_name = statement.split('CREATE TABLE')[1].split('(')[0].strip().split()[2]
                    print(f"✓ Created table: {table_name}")
                elif 'ALTER TABLE' in statement.upper():
                    parts = statement.split()
                    if 'ADD COLUMN' in statement.upper():
                        table_name = parts[2]
                        column_name = parts[5]
                        print(f"✓ Added column {column_name} to {table_name}")
                elif 'CREATE INDEX' in statement.upper():
                    pass  # Skip index messages to reduce clutter
                    
            except sqlite3.OperationalError as e:
                error_msg = str(e)
                # Ignore "duplicate column" and "already exists" errors
                if 'duplicate column' in error_msg.lower() or 'already exists' in error_msg.lower():
                    continue
                else:
                    print(f"⚠️  Warning: {error_msg}")
        
        conn.commit()
        conn.close()
        
        print("=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print("\nNew tables created:")
        print("  - job_analytics")
        print("  - job_external_postings")
        print("  - job_audit_log")
        print("  - bulk_operations")
        print("\nColumns added to jobs table:")
        print("  - archived_at")
        print("  - view_count")
        print("  - application_deadline")
        print("\nYou can now:")
        print("  1. Restart your server if it's running")
        print("  2. Access the dashboard at: http://localhost:8000/jobs-management/dashboard")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(apply_migration())
    exit(0 if success else 1)
