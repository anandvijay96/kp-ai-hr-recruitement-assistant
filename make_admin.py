#!/usr/bin/env python3
"""Make a user admin"""
import sqlite3
import sys

def make_admin(email):
    db_path = "hr_recruitment.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id, full_name, role FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User not found: {email}")
            print()
            print("Available users:")
            cursor.execute("SELECT email, full_name, role FROM users")
            for row in cursor.fetchall():
                print(f"  - {row[0]} ({row[1]}) - Role: {row[2]}")
            conn.close()
            return False
        
        user_id, full_name, current_role = user
        
        if current_role == 'admin':
            print(f"✓ {email} is already an admin!")
            conn.close()
            return True
        
        # Update to admin
        cursor.execute("UPDATE users SET role = 'admin' WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        
        print("=" * 60)
        print(f"✅ SUCCESS!")
        print("=" * 60)
        print()
        print(f"User: {full_name}")
        print(f"Email: {email}")
        print(f"Old Role: {current_role}")
        print(f"New Role: admin")
        print()
        print("You can now login with this account and manage users!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "Kartik@kloudportal.com"
    
    print("=" * 60)
    print("  Make User Admin")
    print("=" * 60)
    print()
    print(f"Making {email} an admin...")
    print()
    
    success = make_admin(email)
    sys.exit(0 if success else 1)
