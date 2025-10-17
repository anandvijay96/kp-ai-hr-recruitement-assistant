"""Test password verification"""
import sqlite3
from services.password_service import PasswordService

def test_password(email, password):
    conn = sqlite3.connect('hr_recruitment.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    
    if not result:
        print(f"❌ User not found: {email}")
        return
    
    password_hash = result[0]
    print(f"Testing password for: {email}")
    print(f"Password: {password}")
    print(f"Hash: {password_hash[:50]}...")
    
    password_service = PasswordService()
    is_valid = password_service.verify_password(password, password_hash)
    
    if is_valid:
        print(f"\n✅ Password is CORRECT!")
    else:
        print(f"\n❌ Password is INCORRECT!")
        print(f"\nTrying to verify what the password might be...")
        
        # Try common passwords
        test_passwords = [
            "Test@12345",
            "test@12345", 
            "Test@123",
            "admin123",
            "password",
            "Recruiter@123"
        ]
        
        for test_pwd in test_passwords:
            if password_service.verify_password(test_pwd, password_hash):
                print(f"✅ Found it! The password is: {test_pwd}")
                break
    
    conn.close()

if __name__ == "__main__":
    import sys
    email = sys.argv[1] if len(sys.argv) > 1 else "vijay@test.com"
    password = sys.argv[2] if len(sys.argv) > 2 else "Test@12345"
    test_password(email, password)
