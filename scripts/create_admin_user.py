"""Create a default admin user"""
import sqlite3
import os
import uuid
from datetime import datetime
import bcrypt

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'hr_recruitment.db')

# Default admin credentials
EMAIL = "admin@bmad.com"
PASSWORD = "admin123"  # Change this after first login!
FULL_NAME = "Admin User"
ROLE = "admin"

print("="*60)
print("🔐 Creating Admin User")
print("="*60)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT email FROM users WHERE email = ?", (EMAIL,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        print(f"⚠️  User with email {EMAIL} already exists!")
        print("   Updating password...")
        
        # Hash password with bcrypt
        password_bytes = PASSWORD.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        # Update existing user's password
        cursor.execute("""
            UPDATE users 
            SET password_hash = ?, updated_at = ?
            WHERE email = ?
        """, (password_hash, datetime.now().isoformat(), EMAIL))
        
        conn.commit()
        print("✅ Password updated successfully!")
    else:
        # Hash password with bcrypt
        password_bytes = PASSWORD.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        user_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO users (
                id, email, password_hash, full_name, role, 
                mobile, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            EMAIL,
            password_hash,
            FULL_NAME,
            ROLE,
            "+1234567890",  # Default mobile
            1,  # is_active = True
            now,
            now
        ))
        
        conn.commit()
        
        print("✅ Admin user created successfully!")
        print("-"*60)
        print(f"📧 Email: {EMAIL}")
        print(f"🔑 Password: {PASSWORD}")
        print(f"👤 Role: {ROLE}")
        print("-"*60)
        print("\n⚠️  IMPORTANT: Change the password after first login!")
        print("\n🔗 Login at: http://localhost:8000/login")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("="*60)
