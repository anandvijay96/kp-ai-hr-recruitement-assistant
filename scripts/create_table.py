"""Create resume_job_matches table directly in SQLite"""
import sqlite3
import os

# Get database path
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'hr_recruitment.db')

print(f"Connecting to database: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create table
print("Creating resume_job_matches table...")

cursor.execute("""
CREATE TABLE IF NOT EXISTS resume_job_matches (
    id TEXT PRIMARY KEY,
    resume_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    match_score INTEGER NOT NULL CHECK (match_score >= 0 AND match_score <= 100),
    skill_score INTEGER CHECK (skill_score >= 0 AND skill_score <= 100),
    experience_score INTEGER CHECK (experience_score >= 0 AND experience_score <= 100),
    education_score INTEGER CHECK (education_score >= 0 AND education_score <= 100),
    matched_skills TEXT,
    missing_skills TEXT,
    match_details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    UNIQUE(resume_id, job_id)
)
""")

print("Creating indexes...")

# Create indexes
cursor.execute("CREATE INDEX IF NOT EXISTS idx_resume_job_matches_resume ON resume_job_matches(resume_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_resume_job_matches_job ON resume_job_matches(job_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_resume_job_matches_score ON resume_job_matches(match_score DESC)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_resume_job_matches_created ON resume_job_matches(created_at DESC)")

# Commit changes
conn.commit()

# Verify table was created
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='resume_job_matches'")
result = cursor.fetchone()

if result:
    print(f"✅ SUCCESS! Table '{result[0]}' created successfully!")
    
    # Show table schema
    cursor.execute("PRAGMA table_info(resume_job_matches)")
    columns = cursor.fetchall()
    print("\nTable schema:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Show indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='resume_job_matches'")
    indexes = cursor.fetchall()
    print(f"\nIndexes created: {len(indexes)}")
    for idx in indexes:
        print(f"  - {idx[0]}")
else:
    print("❌ ERROR: Table was not created!")

# Close connection
conn.close()

print("\nDone!")
