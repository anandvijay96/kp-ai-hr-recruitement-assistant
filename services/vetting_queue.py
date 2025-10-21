"""
Vetting Queue Service - Gemini API Rate Limiting
================================================
Manages vetting queue to prevent exceeding Gemini's 15 requests/minute limit.
Only ONE user can vet at a time, others wait in queue.
"""
import redis
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import asyncio
from core.config import settings

class VettingQueueService:
    """
    Manages vetting queue using Redis.
    
    Features:
    - FIFO queue for fair access
    - Only 1 active vetting session at a time
    - Session timeout (5 minutes)
    - Real-time queue position tracking
    - Automatic session cleanup
    """
    
    def __init__(self):
        """Initialize Redis connection for queue management."""
        self.redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True
        )
        
        # Redis keys
        self.QUEUE_KEY = "vetting:queue"  # List of waiting users
        self.ACTIVE_SESSION_KEY = "vetting:active_session"  # Current vetting user
        self.SESSION_DATA_KEY = "vetting:session:{user_id}"  # Session metadata
        self.RATE_LIMIT_KEY = "vetting:rate_limit:{minute}"  # Request counter
        
        # Configuration
        self.SESSION_TIMEOUT = 300  # 5 minutes
        self.MAX_REQUESTS_PER_MINUTE = 15  # Gemini free tier limit
    
    async def join_queue(self, user_id: str, user_name: str) -> Dict:
        """
        Add user to vetting queue.
        
        Args:
            user_id: User ID
            user_name: User's full name
            
        Returns:
            Dict with queue status
        """
        # Check if user is already in queue
        if self.is_user_in_queue(user_id):
            return {
                "success": False,
                "message": "You are already in the queue",
                "position": self.get_queue_position(user_id)
            }
        
        # Check if user already has active session
        active_user = self.get_active_session()
        if active_user and active_user["user_id"] == user_id:
            return {
                "success": False,
                "message": "You already have an active vetting session",
                "is_active": True
            }
        
        # Add to queue
        queue_entry = {
            "user_id": user_id,
            "user_name": user_name,
            "joined_at": datetime.now().isoformat()
        }
        
        self.redis_client.rpush(self.QUEUE_KEY, json.dumps(queue_entry))
        
        # Try to start session if no one is active
        if not active_user:
            await self.process_next_in_queue()
        
        position = self.get_queue_position(user_id)
        
        return {
            "success": True,
            "message": "Added to queue",
            "position": position,
            "estimated_wait_seconds": position * 60  # Rough estimate
        }
    
    async def start_vetting_session(self, user_id: str, user_name: str) -> Dict:
        """
        Start a vetting session for user.
        
        Args:
            user_id: User ID
            user_name: User's full name
            
        Returns:
            Dict with session status
        """
        # Check if there's already an active session
        active_session = self.get_active_session()
        if active_session:
            if active_session["user_id"] == user_id:
                # User already has active session
                return {
                    "success": True,
                    "message": "Session already active",
                    "session": active_session
                }
            else:
                # Another user is vetting
                return {
                    "success": False,
                    "message": f"Vetting in progress by {active_session['user_name']}",
                    "active_user": active_session["user_name"],
                    "must_wait": True
                }
        
        # Check rate limit
        if not self.check_rate_limit():
            return {
                "success": False,
                "message": "Rate limit reached. Please wait for the next minute.",
                "rate_limit_exceeded": True,
                "retry_after_seconds": self.get_seconds_until_next_minute()
            }
        
        # Start session
        session_data = {
            "user_id": user_id,
            "user_name": user_name,
            "started_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=self.SESSION_TIMEOUT)).isoformat()
        }
        
        # Set active session
        self.redis_client.setex(
            self.ACTIVE_SESSION_KEY,
            self.SESSION_TIMEOUT,
            json.dumps(session_data)
        )
        
        # Store session data
        session_key = self.SESSION_DATA_KEY.format(user_id=user_id)
        self.redis_client.setex(
            session_key,
            self.SESSION_TIMEOUT,
            json.dumps(session_data)
        )
        
        return {
            "success": True,
            "message": "Vetting session started",
            "session": session_data
        }
    
    def end_vetting_session(self, user_id: str) -> Dict:
        """
        End vetting session and process next in queue.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with status
        """
        active_session = self.get_active_session()
        
        if not active_session:
            return {
                "success": False,
                "message": "No active session to end"
            }
        
        if active_session["user_id"] != user_id:
            return {
                "success": False,
                "message": "You don't have an active session"
            }
        
        # Clear active session
        self.redis_client.delete(self.ACTIVE_SESSION_KEY)
        
        # Clear user session data
        session_key = self.SESSION_DATA_KEY.format(user_id=user_id)
        self.redis_client.delete(session_key)
        
        # Process next in queue
        asyncio.create_task(self.process_next_in_queue())
        
        return {
            "success": True,
            "message": "Session ended successfully"
        }
    
    async def process_next_in_queue(self):
        """Process the next user in queue."""
        # Get next user from queue
        queue_entry_json = self.redis_client.lpop(self.QUEUE_KEY)
        
        if not queue_entry_json:
            return  # Queue is empty
        
        queue_entry = json.loads(queue_entry_json)
        user_id = queue_entry["user_id"]
        user_name = queue_entry["user_name"]
        
        # Start session for this user
        await self.start_vetting_session(user_id, user_name)
    
    def get_active_session(self) -> Optional[Dict]:
        """
        Get current active vetting session.
        
        Returns:
            Session data or None
        """
        session_json = self.redis_client.get(self.ACTIVE_SESSION_KEY)
        if not session_json:
            return None
        
        return json.loads(session_json)
    
    def get_queue_status(self) -> Dict:
        """
        Get current queue status.
        
        Returns:
            Dict with queue information
        """
        active_session = self.get_active_session()
        queue_length = self.redis_client.llen(self.QUEUE_KEY)
        
        # Get all queue entries
        queue_entries = []
        for i in range(queue_length):
            entry_json = self.redis_client.lindex(self.QUEUE_KEY, i)
            if entry_json:
                queue_entries.append(json.loads(entry_json))
        
        return {
            "active_session": active_session,
            "queue_length": queue_length,
            "queue_entries": queue_entries,
            "is_available": active_session is None and queue_length == 0
        }
    
    def get_queue_position(self, user_id: str) -> int:
        """
        Get user's position in queue.
        
        Args:
            user_id: User ID
            
        Returns:
            Position (1-indexed) or 0 if not in queue
        """
        queue_length = self.redis_client.llen(self.QUEUE_KEY)
        
        for i in range(queue_length):
            entry_json = self.redis_client.lindex(self.QUEUE_KEY, i)
            if entry_json:
                entry = json.loads(entry_json)
                if entry["user_id"] == user_id:
                    return i + 1  # 1-indexed position
        
        return 0  # Not in queue
    
    def is_user_in_queue(self, user_id: str) -> bool:
        """Check if user is in queue."""
        return self.get_queue_position(user_id) > 0
    
    def leave_queue(self, user_id: str) -> Dict:
        """
        Remove user from queue.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with status
        """
        queue_length = self.redis_client.llen(self.QUEUE_KEY)
        
        for i in range(queue_length):
            entry_json = self.redis_client.lindex(self.QUEUE_KEY, i)
            if entry_json:
                entry = json.loads(entry_json)
                if entry["user_id"] == user_id:
                    # Remove from queue
                    self.redis_client.lrem(self.QUEUE_KEY, 1, entry_json)
                    return {
                        "success": True,
                        "message": "Removed from queue"
                    }
        
        return {
            "success": False,
            "message": "Not in queue"
        }
    
    def check_rate_limit(self) -> bool:
        """
        Check if we can make more API requests this minute.
        
        Returns:
            True if under limit, False if exceeded
        """
        current_minute = datetime.now().strftime("%Y-%m-%d-%H-%M")
        rate_key = self.RATE_LIMIT_KEY.format(minute=current_minute)
        
        # Get current count
        current_count = self.redis_client.get(rate_key)
        if current_count is None:
            current_count = 0
        else:
            current_count = int(current_count)
        
        return current_count < self.MAX_REQUESTS_PER_MINUTE
    
    def increment_rate_limit(self):
        """Increment API request counter for current minute."""
        current_minute = datetime.now().strftime("%Y-%m-%d-%H-%M")
        rate_key = self.RATE_LIMIT_KEY.format(minute=current_minute)
        
        # Increment counter
        self.redis_client.incr(rate_key)
        
        # Set expiry to 60 seconds
        self.redis_client.expire(rate_key, 60)
    
    def get_rate_limit_status(self) -> Dict:
        """
        Get current rate limit status.
        
        Returns:
            Dict with rate limit info
        """
        current_minute = datetime.now().strftime("%Y-%m-%d-%H-%M")
        rate_key = self.RATE_LIMIT_KEY.format(minute=current_minute)
        
        current_count = self.redis_client.get(rate_key)
        if current_count is None:
            current_count = 0
        else:
            current_count = int(current_count)
        
        return {
            "requests_used": current_count,
            "requests_limit": self.MAX_REQUESTS_PER_MINUTE,
            "requests_remaining": max(0, self.MAX_REQUESTS_PER_MINUTE - current_count),
            "limit_exceeded": current_count >= self.MAX_REQUESTS_PER_MINUTE,
            "resets_in_seconds": self.get_seconds_until_next_minute()
        }
    
    def get_seconds_until_next_minute(self) -> int:
        """Get seconds remaining until next minute."""
        now = datetime.now()
        next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        return int((next_minute - now).total_seconds())
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions (called by background task)."""
        active_session = self.get_active_session()
        
        if active_session:
            expires_at = datetime.fromisoformat(active_session["expires_at"])
            if datetime.now() > expires_at:
                # Session expired, remove it
                self.redis_client.delete(self.ACTIVE_SESSION_KEY)
                
                # Process next in queue
                asyncio.create_task(self.process_next_in_queue())


# Global instance
vetting_queue = VettingQueueService()
