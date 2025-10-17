"""Check user password in database"""
import sqlite3
import sys

def check_user(email):
    conn = sqlite3.connect('hr_recruitment.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, full_name, email, password_hash, status, created_at, updated_at
        FROM users
        WHERE email = ?
    """, (email,))
    
    user = cursor.fetchone()
    
    if user:
        print(f"\n✅ User found:")
        print(f"  ID: {user[0]}")
        print(f"  Name: {user[1]}")
        print(f"  Email: {user[2]}")
        print(f"  Password Hash: {user[3][:50]}..." if user[3] else "  Password Hash: None")
        print(f"  Status: {user[4]}")
        print(f"  Created: {user[5]}")
        print(f"  Updated: {user[6]}")
        
        # Check if password hash looks valid
        if user[3] and user[3].startswith('$2b$'):
            print(f"\n✅ Password hash format: Valid (bcrypt)")
        elif user[3] and user[3].startswith('UNSET_'):
            print(f"\n⚠️ Password hash: UNSET (user needs to activate account)")
        else:
            print(f"\n❌ Password hash format: Invalid or missing")
    else:
        print(f"\n❌ User not found: {email}")
    
    conn.close()

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "vijay@test.com"
    check_user(email)
