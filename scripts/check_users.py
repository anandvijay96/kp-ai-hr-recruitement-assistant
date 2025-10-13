"""Check existing users in the database"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'hr_recruitment.db')

print(f"Checking database: {db_path}")
print("="*60)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        print("❌ Users table does not exist!")
        print("\nAvailable tables:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for table in cursor.fetchall():
            print(f"  - {table[0]}")
    else:
        print("✅ Users table exists")
        
        # Get all users
        cursor.execute("SELECT id, email, full_name, role, is_active FROM users")
        users = cursor.fetchall()
        
        if users:
            print(f"\n📋 Found {len(users)} user(s):")
            print("-"*60)
            for user in users:
                user_id, email, full_name, role, is_active = user
                status = "✅ Active" if is_active else "❌ Inactive"
                print(f"Email: {email}")
                print(f"Name: {full_name}")
                print(f"Role: {role}")
                print(f"Status: {status}")
                print(f"ID: {user_id}")
                print("-"*60)
        else:
            print("\n❌ No users found in database!")
            print("\nYou need to create a user account.")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
