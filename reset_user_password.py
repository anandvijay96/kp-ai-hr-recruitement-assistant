"""Reset user password directly in database"""
import sqlite3
from services.password_service import PasswordService
from datetime import datetime

def reset_password(email, new_password):
    conn = sqlite3.connect('hr_recruitment.db')
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id, full_name FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    
    if not result:
        print(f"❌ User not found: {email}")
        return
    
    user_id, full_name = result
    print(f"Found user: {full_name} ({email})")
    
    # Hash the new password
    password_service = PasswordService()
    password_hash = password_service.hash_password(new_password)
    
    print(f"New password: {new_password}")
    print(f"New hash: {password_hash[:50]}...")
    
    # Update the password
    cursor.execute("""
        UPDATE users 
        SET password_hash = ?, updated_at = ?
        WHERE id = ?
    """, (password_hash, datetime.utcnow().isoformat(), user_id))
    
    conn.commit()
    
    print(f"\n✅ Password updated successfully!")
    print(f"You can now login with:")
    print(f"  Email: {email}")
    print(f"  Password: {new_password}")
    
    # Verify it works
    is_valid = password_service.verify_password(new_password, password_hash)
    if is_valid:
        print(f"\n✅ Verification: Password is correct!")
    else:
        print(f"\n❌ Verification: Something went wrong!")
    
    conn.close()

if __name__ == "__main__":
    import sys
    email = sys.argv[1] if len(sys.argv) > 1 else "vijay@test.com"
    password = sys.argv[2] if len(sys.argv) > 2 else "Test@12345"
    
    print(f"Resetting password for {email}...")
    reset_password(email, password)
