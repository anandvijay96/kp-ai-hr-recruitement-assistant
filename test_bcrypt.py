"""Test script to verify bcrypt is working"""
import sys

print("Testing bcrypt installation...")

try:
    import bcrypt
    print("✓ bcrypt imported successfully")
    print(f"  bcrypt version: {bcrypt.__version__}")
except ImportError as e:
    print(f"✗ Failed to import bcrypt: {e}")
    sys.exit(1)

try:
    # Test password hashing
    test_password = "TestPassword123!"
    print(f"\nTesting password hashing with: '{test_password}'")
    
    # Hash the password
    password_bytes = test_password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=10)
    hashed = bcrypt.hashpw(password_bytes, salt)
    hashed_str = hashed.decode('utf-8')
    
    print(f"✓ Password hashed successfully")
    print(f"  Hash length: {len(hashed_str)}")
    print(f"  Hash: {hashed_str[:30]}...")
    
    # Test password verification
    is_valid = bcrypt.checkpw(password_bytes, hashed)
    print(f"\n✓ Password verification: {is_valid}")
    
    # Test with wrong password
    wrong_password = "WrongPassword456!"
    wrong_bytes = wrong_password.encode('utf-8')
    is_invalid = bcrypt.checkpw(wrong_bytes, hashed)
    print(f"✓ Wrong password verification: {is_invalid} (should be False)")
    
    print("\n✅ All bcrypt tests passed!")
    
except Exception as e:
    print(f"\n✗ Error during bcrypt test: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
