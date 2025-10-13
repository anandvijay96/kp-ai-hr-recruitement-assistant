"""Fix admin user status"""
import sqlite3
import os
from datetime import datetime

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'hr_recruitment.db')

EMAIL = "admin@bmad.com"

print("="*60)
print("🔧 Fixing Admin User Status")
print("="*60)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check current status
    cursor.execute("SELECT id, email, status, is_active FROM users WHERE email = ?", (EMAIL,))
    user = cursor.fetchone()

    if not user:
        print(f"\n❌ User {EMAIL} not found!")
    else:
        user_id, email, status, is_active = user
        print(f"\n📋 Current User Status:")
        print(f"   Email: {email}")
        print(f"   Status: {status}")
        print(f"   Is Active: {is_active}")

        if status != 'active' or not is_active:
            print(f"\n⚠️  Fixing status to 'active' and is_active to True...")
            cursor.execute("""
                UPDATE users
                SET status = 'active', is_active = 1, updated_at = ?
                WHERE email = ?
            """, (datetime.now().isoformat(), EMAIL))

            conn.commit()
            print("✅ Admin user status fixed!")

            # Verify the fix
            cursor.execute("SELECT status, is_active FROM users WHERE email = ?", (EMAIL,))
            fixed_status, fixed_active = cursor.fetchone()
            print(f"✅ New Status: {fixed_status}")
            print(f"✅ New Is Active: {fixed_active}")
        else:
            print("\n✅ Status is already correct - no changes needed")

    conn.close()

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("🎯 Next Steps:")
print("1. Refresh the Users page")
print("2. Try creating a user again")
print("="*60)
