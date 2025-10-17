"""Check recent activities"""
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('hr_recruitment.db')
cursor = conn.cursor()

print("📋 Recent activity logs (last 5):\n")
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
    LIMIT 5
""")

activities = cursor.fetchall()
for act in activities:
    print(f"User: {act[0]}")
    print(f"Action: {act[1]}")
    print(f"Entity: {act[2]}")
    print(f"Time: {act[3]}")
    print(f"Status: {act[4]}")
    print(f"Path: {act[5]}")
    print()

# Check today's count
print("\n📊 Today's stats:")
today = datetime.now().date().isoformat()
cursor.execute("""
    SELECT COUNT(*) 
    FROM user_activity_log 
    WHERE DATE(timestamp) = ?
""", (today,))
print(f"Total activities today: {cursor.fetchone()[0]}")

cursor.execute("""
    SELECT COUNT(*) 
    FROM user_activity_log 
    WHERE action_type = 'vet_resume'
    AND DATE(timestamp) = ?
""", (today,))
print(f"Resumes vetted today: {cursor.fetchone()[0]}")

# Check active users
five_min_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
cursor.execute("""
    SELECT COUNT(DISTINCT user_id)
    FROM user_activity_log
    WHERE timestamp >= ?
""", (five_min_ago,))
print(f"Active users (last 5 min): {cursor.fetchone()[0]}")

conn.close()
