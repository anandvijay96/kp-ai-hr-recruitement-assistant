"""
Test script to diagnose vetting queue system issues
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_queue_system():
    """Test the vetting queue system"""
    print("="*60)
    print("🔍 TESTING VETTING QUEUE SYSTEM")
    print("="*60)
    
    # Test 1: Redis Connection
    print("\n1️⃣ Testing Redis Connection...")
    try:
        import redis
        from core.config import settings
        
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        redis_client.ping()
        print("   ✅ Redis connection successful")
        print(f"   📍 Redis URL: {settings.redis_url}")
    except Exception as e:
        print(f"   ❌ Redis connection failed: {e}")
        print("   💡 Make sure Redis is running: redis-server")
        return False
    
    # Test 2: Import Queue Service
    print("\n2️⃣ Testing Queue Service Import...")
    try:
        from services.vetting_queue import vetting_queue
        print("   ✅ Queue service imported successfully")
    except Exception as e:
        print(f"   ❌ Failed to import queue service: {e}")
        return False
    
    # Test 3: Get Queue Status
    print("\n3️⃣ Testing Queue Status...")
    try:
        status = vetting_queue.get_queue_status()
        print(f"   ✅ Queue status retrieved")
        print(f"   📊 Active session: {status['active_session']}")
        print(f"   📊 Queue length: {status['queue_length']}")
        print(f"   📊 Is available: {status['is_available']}")
    except Exception as e:
        print(f"   ❌ Failed to get queue status: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Rate Limit Check
    print("\n4️⃣ Testing Rate Limit...")
    try:
        rate_limit = vetting_queue.get_rate_limit_status()
        print(f"   ✅ Rate limit status retrieved")
        print(f"   📊 Requests used: {rate_limit['requests_used']}/{rate_limit['requests_limit']}")
        print(f"   📊 Requests remaining: {rate_limit['requests_remaining']}")
        print(f"   📊 Limit exceeded: {rate_limit['limit_exceeded']}")
    except Exception as e:
        print(f"   ❌ Failed to check rate limit: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Join Queue (Test User)
    print("\n5️⃣ Testing Join Queue...")
    try:
        result = await vetting_queue.join_queue("test_user_1", "Test User 1")
        print(f"   ✅ Join queue result: {result['message']}")
        print(f"   📊 Success: {result['success']}")
        if 'position' in result:
            print(f"   📊 Position: {result['position']}")
    except Exception as e:
        print(f"   ❌ Failed to join queue: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 6: Check Active Session
    print("\n6️⃣ Testing Active Session...")
    try:
        active = vetting_queue.get_active_session()
        if active:
            print(f"   ✅ Active session found")
            print(f"   📊 User: {active['user_name']}")
            print(f"   📊 Started: {active['started_at']}")
        else:
            print(f"   ℹ️  No active session")
    except Exception as e:
        print(f"   ❌ Failed to check active session: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 7: End Session (Cleanup)
    print("\n7️⃣ Cleaning up test session...")
    try:
        if active:
            result = vetting_queue.end_vetting_session(active['user_id'])
            print(f"   ✅ Session ended: {result['message']}")
        else:
            print(f"   ℹ️  No session to end")
    except Exception as e:
        print(f"   ⚠️  Cleanup warning: {e}")
    
    # Test 8: API Endpoints
    print("\n8️⃣ Testing API Endpoints...")
    try:
        from api.v1 import vetting_queue as vetting_queue_api
        print("   ✅ API endpoints imported successfully")
    except Exception as e:
        print(f"   ❌ Failed to import API endpoints: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - Queue system is functional!")
    print("="*60)
    return True

if __name__ == "__main__":
    result = asyncio.run(test_queue_system())
    sys.exit(0 if result else 1)
