"""Check and fix admin user role"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'hr_recruitment.db')

EMAIL = "admin@bmad.com"

print("="*60)
print("🔍 Checking Admin User Role")
print("="*60)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current role
    cursor.execute("SELECT id, email, full_name, role FROM users WHERE email = ?", (EMAIL,))
    user = cursor.fetchone()
    
    if not user:
        print(f"\n❌ User {EMAIL} not found!")
    else:
        user_id, email, full_name, role = user
        print(f"\n📋 Current User Info:")
        print(f"   Email: {email}")
        print(f"   Name: {full_name}")
        print(f"   Role: {role}")
        
        if role != 'admin':
            print(f"\n⚠️  Role is '{role}' but should be 'admin'")
            print("   Fixing...")
            
            cursor.execute("""
                UPDATE users 
                SET role = 'admin'
                WHERE email = ?
            """, (EMAIL,))
            
            conn.commit()
            print("✅ Role updated to 'admin'!")
        else:
            print("\n✅ Role is already 'admin' - no changes needed")
    
    conn.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Please logout and login again to see the changes")
print("="*60)
