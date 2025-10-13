"""Fix admin user - add missing fields"""
import sqlite3
import os
from datetime import datetime

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'hr_recruitment.db')

EMAIL = "admin@bmad.com"

print("="*60)
print("🔧 Fixing Admin User Fields")
print("="*60)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current user fields
    cursor.execute("PRAGMA table_info(users)")
    columns = {col[1] for col in cursor.fetchall()}
    print(f"\n📋 Current columns: {columns}")
    
    # Get user
    cursor.execute("SELECT id, email FROM users WHERE email = ?", (EMAIL,))
    user = cursor.fetchone()
    
    if not user:
        print(f"\n❌ User {EMAIL} not found!")
    else:
        user_id, email = user
        print(f"\n✅ Found user: {email}")
        
        # Add missing columns if they don't exist
        missing_columns = []
        
        if 'failed_login_attempts' not in columns:
            print("   Adding failed_login_attempts column...")
            cursor.execute("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0")
            missing_columns.append('failed_login_attempts')
        
        if 'login_count' not in columns:
            print("   Adding login_count column...")
            cursor.execute("ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0")
            missing_columns.append('login_count')
        
        if 'last_login' not in columns:
            print("   Adding last_login column...")
            cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
            missing_columns.append('last_login')
        
        if 'account_locked_until' not in columns:
            print("   Adding account_locked_until column...")
            cursor.execute("ALTER TABLE users ADD COLUMN account_locked_until TIMESTAMP")
            missing_columns.append('account_locked_until')
        
        if 'email_verified' not in columns:
            print("   Adding email_verified column...")
            cursor.execute("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 1")
            missing_columns.append('email_verified')
        
        if 'email_verification_token' not in columns:
            print("   Adding email_verification_token column...")
            cursor.execute("ALTER TABLE users ADD COLUMN email_verification_token TEXT")
            missing_columns.append('email_verification_token')
        
        # Update existing user to ensure all fields have values
        cursor.execute("""
            UPDATE users 
            SET 
                failed_login_attempts = COALESCE(failed_login_attempts, 0),
                login_count = COALESCE(login_count, 0),
                email_verified = COALESCE(email_verified, 1),
                updated_at = ?
            WHERE email = ?
        """, (datetime.now().isoformat(), EMAIL))
        
        conn.commit()
        
        if missing_columns:
            print(f"\n✅ Added {len(missing_columns)} missing columns:")
            for col in missing_columns:
                print(f"   - {col}")
        else:
            print("\n✅ All columns already exist")
        
        print(f"\n✅ User {email} fixed successfully!")
        
        # Verify
        cursor.execute("""
            SELECT failed_login_attempts, login_count, email_verified, is_active 
            FROM users WHERE email = ?
        """, (EMAIL,))
        result = cursor.fetchone()
        print(f"\n📊 User status:")
        print(f"   - failed_login_attempts: {result[0]}")
        print(f"   - login_count: {result[1]}")
        print(f"   - email_verified: {result[2]}")
        print(f"   - is_active: {result[3]}")
    
    conn.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
