"""
Script to add candidate_ratings table to database
"""
import sqlite3

# Connect to database
conn = sqlite3.connect('hr_recruitment.db')
cursor = conn.cursor()

try:
    # Create candidate_ratings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_ratings (
            id TEXT PRIMARY KEY,
            candidate_id TEXT NOT NULL,
            user_id TEXT,
            technical_skills INTEGER CHECK(technical_skills >= 1 AND technical_skills <= 5),
            communication INTEGER CHECK(communication >= 1 AND communication <= 5),
            culture_fit INTEGER CHECK(culture_fit >= 1 AND culture_fit <= 5),
            experience_level INTEGER CHECK(experience_level >= 1 AND experience_level <= 5),
            overall_rating INTEGER CHECK(overall_rating >= 1 AND overall_rating <= 5),
            comments TEXT,
            strengths TEXT,
            concerns TEXT,
            recommendation TEXT CHECK(recommendation IN ('highly_recommended', 'recommended', 'maybe', 'not_recommended')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ratings_candidate ON candidate_ratings(candidate_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ratings_user ON candidate_ratings(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ratings_overall ON candidate_ratings(overall_rating)")
    
    conn.commit()
    print("✅ Successfully created candidate_ratings table and indexes")
except sqlite3.Error as e:
    print(f"❌ Error: {e}")
finally:
    conn.close()
