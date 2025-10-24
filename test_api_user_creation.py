"""
Test user creation via the actual API endpoint to verify the fix works end-to-end
"""
import asyncio
import httpx
from services.password_service import PasswordService
from core.database import AsyncSessionLocal
from models.database import User
from sqlalchemy import select

async def test_api_user_creation():
    print("="*60)
    print("🧪 TESTING USER CREATION VIA API")
    print("="*60)
    
    # Step 1: Login as admin to get token
    print("\n1️⃣ Logging in as admin...")
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        login_response = await client.post("/api/auth/login", json={
            "email": "admin@bmad.com",
            "password": "admin"  # Try common passwords
        })
        
        if login_response.status_code != 200:
            # Try other passwords
            for pwd in ["admin123", "Admin@123", "password"]:
                login_response = await client.post("/api/auth/login", json={
                    "email": "admin@bmad.com",
                    "password": pwd
                })
                if login_response.status_code == 200:
                    break
        
        if login_response.status_code != 200:
            print(f"   ❌ Admin login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            print(f"   ⚠️  Cannot test API without admin token")
            return False
        
        token_data = login_response.json()
        access_token = token_data["data"]["tokens"]["access_token"]
        print(f"   ✅ Admin logged in successfully")
        
        # Step 2: Create a new user via API
        print(f"\n2️⃣ Creating new user via API...")
        test_email = f"apitest_{asyncio.get_event_loop().time()}@test.com"
        test_password = "ApiTest@123"
        
        create_response = await client.post(
            "/api/users",
            json={
                "full_name": "API Test User",
                "email": test_email,
                "mobile": "+1234567890",
                "role": "recruiter",
                "department": "Engineering",
                "status": "active",
                "password": test_password  # THIS IS THE CRITICAL FIELD
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if create_response.status_code != 201:
            print(f"   ❌ User creation failed: {create_response.status_code}")
            print(f"   Response: {create_response.text}")
            return False
        
        result = create_response.json()
        print(f"   ✅ User created successfully")
        print(f"   Email: {result['email']}")
        print(f"   Password set: {test_password}")
        
        # Step 3: Try to login with the new user
        print(f"\n3️⃣ Testing login with new user...")
        login_test = await client.post("/api/auth/login", json={
            "email": test_email,
            "password": test_password
        })
        
        if login_test.status_code == 200:
            print(f"   ✅ LOGIN SUCCESSFUL!")
            print(f"   The fix is working! User can login with the password set during creation.")
            return True
        else:
            print(f"   ❌ LOGIN FAILED: {login_test.status_code}")
            print(f"   Response: {login_test.text}")
            
            # Step 4: Check the database to see what password was actually stored
            print(f"\n4️⃣ Checking database...")
            async with AsyncSessionLocal() as db:
                user_result = await db.execute(
                    select(User).where(User.email == test_email)
                )
                user = user_result.scalar_one_or_none()
                
                if user:
                    print(f"   User found in database:")
                    print(f"   Hash: {user.password_hash[:40]}...")
                    
                    # Test password verification
                    password_service = PasswordService()
                    is_valid = password_service.verify_password(test_password, user.password_hash)
                    print(f"   Direct verification: {'✅ VALID' if is_valid else '❌ INVALID'}")
                    
                    if not is_valid:
                        print(f"\n   ❌ THE FIX DID NOT WORK!")
                        print(f"   The password field is still being ignored")
                else:
                    print(f"   ❌ User not found in database")
            
            return False

if __name__ == "__main__":
    result = asyncio.run(test_api_user_creation())
    print("\n" + "="*60)
    if result:
        print("✅ API USER CREATION FIX IS WORKING!")
    else:
        print("❌ API USER CREATION FIX IS NOT WORKING!")
    print("="*60)
