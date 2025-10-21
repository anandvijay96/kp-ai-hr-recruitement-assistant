"""
Redis-based LLM Usage Tracker - Production-ready tracking with Redis
Replaces JSON file-based tracking for better reliability and performance
"""

import logging
import redis
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from core.config import settings

logger = logging.getLogger(__name__)


class RedisLLMUsageTracker:
    """
    Redis-based LLM Usage Tracker
    
    Features:
    - Real-time usage tracking with atomic operations
    - Automatic daily reset using Redis TTL
    - No file I/O overhead
    - Thread-safe by design
    - Perfect for multi-container deployments
    
    Redis Keys Structure:
    - llm:gemini:requests:{date} → Request count
    - llm:gemini:tokens:{date} → Token count
    - llm:openai:requests:{date} → Request count
    - llm:openai:tokens:{date} → Token count
    - llm:openai:cost:{date} → Cost in USD
    - llm:minute:gemini → Minute-level request tracking (60s TTL)
    - llm:minute:openai → Minute-level request tracking (60s TTL)
    """
    
    # Gemini Free Tier Limits (Updated Oct 2025)
    GEMINI_FREE_RPM = 15  # Requests per minute
    GEMINI_FREE_RPD = 1000  # Requests per day (Gemini 2.5 Flash-Lite)
    GEMINI_FREE_TPM = 250_000  # Tokens per minute
    
    # OpenAI Pricing (GPT-4o-mini)
    OPENAI_INPUT_COST_PER_1M = 0.15  # $0.15 per 1M input tokens
    OPENAI_OUTPUT_COST_PER_1M = 0.60  # $0.60 per 1M output tokens
    
    def __init__(self, redis_url: str = None):
        """Initialize Redis connection"""
        self.redis_url = redis_url or settings.redis_url
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"✅ Redis LLM Usage Tracker connected to {self.redis_url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    def _get_today_key(self) -> str:
        """Get today's date key (YYYY-MM-DD)"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def _get_redis_key(self, provider: str, metric: str) -> str:
        """
        Generate Redis key
        
        Args:
            provider: 'gemini' or 'openai'
            metric: 'requests', 'tokens', 'cost'
        
        Returns:
            Redis key like 'llm:gemini:requests:2025-10-21'
        """
        date_key = self._get_today_key()
        return f"llm:{provider}:{metric}:{date_key}"
    
    def _get_minute_key(self, provider: str) -> str:
        """Get minute-level tracking key"""
        return f"llm:minute:{provider}"
    
    def _ensure_key_expiry(self, key: str):
        """Set key to expire at midnight (end of day)"""
        try:
            # Calculate seconds until midnight
            now = datetime.now()
            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            seconds_until_midnight = int((tomorrow - now).total_seconds())
            
            # Set expiry if not already set
            if self.redis_client.ttl(key) == -1:  # -1 means no expiry
                self.redis_client.expire(key, seconds_until_midnight)
        except Exception as e:
            logger.error(f"Error setting key expiry: {e}")
    
    def track_request(
        self,
        provider: str,
        success: bool,
        tokens_used: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0
    ):
        """
        Track an LLM API request
        
        Args:
            provider: 'gemini' or 'openai'
            success: Whether request succeeded
            tokens_used: Total tokens (for Gemini)
            input_tokens: Input tokens (for OpenAI)
            output_tokens: Output tokens (for OpenAI)
        """
        try:
            provider = provider.lower()
            
            if not success:
                # Don't track failed requests in quota
                logger.warning(f"Failed {provider} request not tracked in quota")
                return
            
            # Track requests
            requests_key = self._get_redis_key(provider, "requests")
            self.redis_client.incr(requests_key)
            self._ensure_key_expiry(requests_key)
            
            # Track minute-level requests (for rate limiting)
            minute_key = self._get_minute_key(provider)
            self.redis_client.incr(minute_key)
            self.redis_client.expire(minute_key, 60)  # Expire after 60 seconds
            
            # Provider-specific tracking
            if provider == "gemini":
                # Track tokens
                tokens_key = self._get_redis_key("gemini", "tokens")
                self.redis_client.incrby(tokens_key, tokens_used)
                self._ensure_key_expiry(tokens_key)
                
            elif provider == "openai":
                # Track tokens
                total_tokens = input_tokens + output_tokens
                tokens_key = self._get_redis_key("openai", "tokens")
                self.redis_client.incrby(tokens_key, total_tokens)
                self._ensure_key_expiry(tokens_key)
                
                # Calculate and track cost
                input_cost = (input_tokens / 1_000_000) * self.OPENAI_INPUT_COST_PER_1M
                output_cost = (output_tokens / 1_000_000) * self.OPENAI_OUTPUT_COST_PER_1M
                total_cost = input_cost + output_cost
                
                cost_key = self._get_redis_key("openai", "cost")
                self.redis_client.incrbyfloat(cost_key, total_cost)
                self._ensure_key_expiry(cost_key)
            
            logger.info(f"📊 Tracked {provider} request: tokens={tokens_used or (input_tokens + output_tokens)}")
            
        except Exception as e:
            logger.error(f"Error tracking request: {e}")
    
    def can_make_request(self, provider: str = "gemini") -> Tuple[bool, Optional[str]]:
        """
        Check if request can be made without exceeding limits
        
        Returns:
            (can_proceed, warning_message)
        """
        try:
            if provider.lower() == "gemini":
                return self._check_gemini_limits()
            else:
                # OpenAI has no free tier, just track usage
                return True, None
        except Exception as e:
            logger.error(f"Error checking limits: {e}")
            return True, None  # Allow request on error
    
    def _check_gemini_limits(self) -> Tuple[bool, Optional[str]]:
        """Check Gemini free tier limits"""
        try:
            # Check RPM (Requests Per Minute)
            minute_key = self._get_minute_key("gemini")
            rpm_count = int(self.redis_client.get(minute_key) or 0)
            
            if rpm_count >= self.GEMINI_FREE_RPM:
                return False, f"⚠️ Gemini RPM limit reached ({rpm_count}/{self.GEMINI_FREE_RPM}). Wait 1 minute."
            
            # Check RPD (Requests Per Day)
            requests_key = self._get_redis_key("gemini", "requests")
            rpd_count = int(self.redis_client.get(requests_key) or 0)
            
            if rpd_count >= self.GEMINI_FREE_RPD:
                return False, f"❌ Gemini daily limit reached ({rpd_count}/{self.GEMINI_FREE_RPD}). Try tomorrow or switch accounts."
            
            # Warnings at 80% and 90%
            usage_percent = (rpd_count / self.GEMINI_FREE_RPD) * 100
            if usage_percent >= 90:
                return True, f"🔴 Critical: {usage_percent:.0f}% of daily quota used ({rpd_count}/{self.GEMINI_FREE_RPD})"
            elif usage_percent >= 80:
                return True, f"🟡 Warning: {usage_percent:.0f}% of daily quota used ({rpd_count}/{self.GEMINI_FREE_RPD})"
            elif usage_percent >= 50:
                return True, f"🟢 {usage_percent:.0f}% of daily quota used ({rpd_count}/{self.GEMINI_FREE_RPD})"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking Gemini limits: {e}")
            return True, None  # Allow request on error
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current usage summary"""
        try:
            # Get Gemini stats
            gemini_requests = int(self.redis_client.get(self._get_redis_key("gemini", "requests")) or 0)
            gemini_tokens = int(self.redis_client.get(self._get_redis_key("gemini", "tokens")) or 0)
            gemini_rpm = int(self.redis_client.get(self._get_minute_key("gemini")) or 0)
            
            # Get OpenAI stats
            openai_requests = int(self.redis_client.get(self._get_redis_key("openai", "requests")) or 0)
            openai_tokens = int(self.redis_client.get(self._get_redis_key("openai", "tokens")) or 0)
            openai_cost = float(self.redis_client.get(self._get_redis_key("openai", "cost")) or 0.0)
            
            # Calculate usage percentages
            gemini_daily_percent = (gemini_requests / self.GEMINI_FREE_RPD) * 100
            
            # Determine status
            if gemini_daily_percent >= 90:
                status = "critical"
                status_emoji = "🔴"
            elif gemini_daily_percent >= 80:
                status = "warning"
                status_emoji = "🟡"
            elif gemini_daily_percent >= 50:
                status = "moderate"
                status_emoji = "🟢"
            else:
                status = "healthy"
                status_emoji = "✅"
            
            return {
                "status": status,
                "status_emoji": status_emoji,
                "total_requests": gemini_requests + openai_requests,
                "successful_requests": gemini_requests + openai_requests,  # Only successful tracked
                "failed_requests": 0,  # Not tracked separately
                "gemini": {
                    "requests_today": gemini_requests,
                    "daily_limit": self.GEMINI_FREE_RPD,
                    "remaining": max(0, self.GEMINI_FREE_RPD - gemini_requests),
                    "usage_percent": round(gemini_daily_percent, 1),
                    "tokens_used": gemini_tokens,
                    "requests_per_minute": gemini_rpm
                },
                "openai": {
                    "requests_total": openai_requests,
                    "tokens_used": openai_tokens,
                    "cost_usd": round(openai_cost, 4)
                },
                "total_cost_usd": round(openai_cost, 4),
                "last_reset": self._get_today_key(),
                "storage": "redis"  # Indicator that this is Redis-based
            }
            
        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")
            # Return empty stats on error
            return {
                "status": "error",
                "status_emoji": "❌",
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "gemini": {
                    "requests_today": 0,
                    "daily_limit": self.GEMINI_FREE_RPD,
                    "remaining": self.GEMINI_FREE_RPD,
                    "usage_percent": 0,
                    "tokens_used": 0,
                    "requests_per_minute": 0
                },
                "openai": {
                    "requests_total": 0,
                    "tokens_used": 0,
                    "cost_usd": 0.0
                },
                "total_cost_usd": 0.0,
                "last_reset": self._get_today_key(),
                "storage": "redis",
                "error": str(e)
            }
    
    def reset_stats(self):
        """Reset all statistics (admin function)"""
        try:
            date_key = self._get_today_key()
            
            # Delete all keys for today
            keys_to_delete = [
                f"llm:gemini:requests:{date_key}",
                f"llm:gemini:tokens:{date_key}",
                f"llm:openai:requests:{date_key}",
                f"llm:openai:tokens:{date_key}",
                f"llm:openai:cost:{date_key}",
                "llm:minute:gemini",
                "llm:minute:openai"
            ]
            
            for key in keys_to_delete:
                self.redis_client.delete(key)
            
            logger.info("🔄 Usage statistics reset")
            
        except Exception as e:
            logger.error(f"Error resetting stats: {e}")
    
    def health_check(self) -> bool:
        """Check if Redis connection is healthy"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global tracker instance
_redis_tracker_instance = None


def get_redis_tracker() -> RedisLLMUsageTracker:
    """Get global Redis tracker instance"""
    global _redis_tracker_instance
    if _redis_tracker_instance is None:
        _redis_tracker_instance = RedisLLMUsageTracker()
    return _redis_tracker_instance
