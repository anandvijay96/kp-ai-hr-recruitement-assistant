"""
Create initial admin user for User Management feature
Run with: python create_admin_user.py
"""
import sqlite3
import uuid
from datetime import datetime

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    import hashlib
    HAS_BCRYPT = False
    print("⚠️  Warning: bcrypt not installed, using SHA-256 (not secure for production)")

def hash_password(password: str) -> str:
    """Hash password using bcrypt or fallback to SHA-256"""
    if HAS_BCRYPT:
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    else:
        return hashlib.sha256(password.encode()).hexdigest()

def create_admin_user():
    """Create initial admin user"""
    
    db_path = "hr_recruitment.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("❌ Users table does not exist. Please run the migration first:")
            print("   python apply_migration.py migrations/010_create_user_management_tables.sql")
            conn.close()
            return False
        
        # Check if admin user already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@example.com",))
        if cursor.fetchone():
            print("✓ Admin user already exists: admin@example.com")
            conn.close()
            return True
        
        # Create admin user
        user_id = str(uuid.uuid4())
        password_hash = hash_password("Admin@123")  # Default password
        created_at = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO users (
                id, full_name, email, password_hash, role, status, 
                is_active, email_verified, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            "Admin User",
            "admin@example.com",
            password_hash,
            "admin",
            "active",
            1,  # is_active
            1,  # email_verified
            created_at,
            created_at
        ))
        
        conn.commit()
        conn.close()
        
        print("=" * 60)
        print("✅ Initial admin user created successfully!")
        print("=" * 60)
        print("\nLogin Credentials:")
        print(f"  Email: admin@example.com")
        print(f"  Password: Admin@123")
        print("\n⚠️  IMPORTANT: Change this password after first login!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_admin_user()
    exit(0 if success else 1)
