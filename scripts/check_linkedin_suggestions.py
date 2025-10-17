"""
Check LinkedIn suggestions in database
"""
import sqlite3
import json

conn = sqlite3.connect('hr_recruitment.db')
cursor = conn.cursor()

# Check if column exists
cursor.execute("PRAGMA table_info(candidates)")
columns = cursor.fetchall()
print("Candidates table columns:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

print("\n" + "="*60)

# Get candidate data
cursor.execute("""
    SELECT id, full_name, email, linkedin_url, linkedin_suggestions 
    FROM candidates 
    WHERE email = 'lahariofficial799@gmail.com'
""")
result = cursor.fetchone()

if result:
    print("\nCandidate Data:")
    print(f"ID: {result[0]}")
    print(f"Name: {result[1]}")
    print(f"Email: {result[2]}")
    print(f"LinkedIn URL: {result[3]}")
    print(f"LinkedIn Suggestions (raw): {result[4]}")
    
    if result[4]:
        try:
            suggestions = json.loads(result[4])
            print(f"\nParsed Suggestions ({len(suggestions)} items):")
            for i, url in enumerate(suggestions, 1):
                print(f"  {i}. {url}")
        except:
            print("\nFailed to parse suggestions as JSON")
    else:
        print("\nLinkedIn Suggestions: NULL or empty")
else:
    print("\nCandidate not found!")

conn.close()
