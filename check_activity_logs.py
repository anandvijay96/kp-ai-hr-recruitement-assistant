"""Check activity logs in database"""
import sqlite3
from datetime import datetime, timedelta

def check_activity_logs():
    conn = sqlite3.connect('hr_recruitment.db')
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_activity_logs'")
    if not cursor.fetchone():
        print("❌ user_activity_logs table does not exist!")
        conn.close()
        return
    
    print("✅ user_activity_logs table exists\n")
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM user_activity_logs")
    total = cursor.fetchone()[0]
    print(f"📊 Total activity logs: {total}\n")
    
    if total == 0:
        print("❌ No activity logs found!")
        print("\nPossible reasons:")
        print("1. Middleware not extracting user_id from session")
        print("2. Session not being set on login")
        print("3. Activity logging failing silently")
        conn.close()
        return
    
    # Get recent activities
    print("📋 Recent activities (last 10):")
    cursor.execute("""
        SELECT 
            id,
            user_id,
            action_type,
            entity_type,
            entity_id,
            created_at,
            duration_ms,
            status
        FROM user_activity_logs
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    activities = cursor.fetchall()
    for act in activities:
        print(f"\n  ID: {act[0]}")
        print(f"  User: {act[1]}")
        print(f"  Action: {act[2]}")
        print(f"  Entity: {act[3]} ({act[4]})")
        print(f"  Time: {act[5]}")
        print(f"  Duration: {act[6]}ms")
        print(f"  Status: {act[7]}")
    
    # Get today's stats
    today = datetime.now().date()
    cursor.execute("""
        SELECT COUNT(*) 
        FROM user_activity_logs 
        WHERE DATE(created_at) = ?
    """, (today,))
    today_count = cursor.fetchone()[0]
    print(f"\n📊 Today's activities: {today_count}")
    
    # Get vetting count
    cursor.execute("""
        SELECT COUNT(*) 
        FROM user_activity_logs 
        WHERE action_type = 'vet_resume'
        AND DATE(created_at) = ?
    """, (today,))
    vetting_count = cursor.fetchone()[0]
    print(f"📊 Resumes vetted today: {vetting_count}")
    
    # Get active users (last 5 minutes)
    five_min_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
    cursor.execute("""
        SELECT COUNT(DISTINCT user_id)
        FROM user_activity_logs
        WHERE created_at >= ?
    """, (five_min_ago,))
    active_users = cursor.fetchone()[0]
    print(f"📊 Active users (last 5 min): {active_users}")
    
    conn.close()

if __name__ == "__main__":
    check_activity_logs()
