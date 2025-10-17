"""Check all activities without date filter"""
import sqlite3

conn = sqlite3.connect('hr_recruitment.db')
cursor = conn.cursor()

print("📋 ALL activity logs (last 20):\n")
cursor.execute("""
    SELECT 
        user_id,
        action_type,
        entity_type,
        timestamp,
        status,
        request_path
    FROM user_activity_log
    ORDER BY timestamp DESC
    LIMIT 20
""")

activities = cursor.fetchall()
for i, act in enumerate(activities, 1):
    print(f"{i}. User: {act[0][:8]}...")
    print(f"   Action: {act[1]}")
    print(f"   Entity: {act[2]}")
    print(f"   Time: {act[3]}")
    print(f"   Path: {act[5]}")
    print()

# Check total count
cursor.execute("SELECT COUNT(*) FROM user_activity_log")
print(f"\n📊 Total activities in database: {cursor.fetchone()[0]}")

# Check vet_resume actions
cursor.execute("SELECT COUNT(*) FROM user_activity_log WHERE action_type = 'vet_resume'")
print(f"📊 Total vet_resume actions: {cursor.fetchone()[0]}")

# Check create_interview actions  
cursor.execute("SELECT COUNT(*) FROM user_activity_log WHERE action_type LIKE '%interview%'")
print(f"📊 Total interview actions: {cursor.fetchone()[0]}")

conn.close()
