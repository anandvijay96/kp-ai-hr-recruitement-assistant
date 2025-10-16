"""
LLM Usage Tracker - Monitor API calls and quota limits
Tracks Gemini and OpenAI usage with real-time monitoring
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class UsageStats:
    """Statistics for LLM usage"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    last_reset: str = ""
    
    # Gemini specific
    gemini_requests: int = 0
    gemini_tokens: int = 0
    
    # OpenAI specific
    openai_requests: int = 0
    openai_tokens: int = 0
    openai_cost: float = 0.0


class LLMUsageTracker:
    """
    Track LLM API usage with quota monitoring
    
    Features:
    - Real-time usage tracking
    - Quota limit warnings
    - Daily/monthly statistics
    - Cost estimation
    - Multi-provider support (Gemini, OpenAI)
    """
    
    # Gemini Free Tier Limits (Updated Oct 2025)
    # Source: https://ai.google.dev/gemini-api/docs/rate-limits
    # Using Gemini 2.5 Flash-Lite (highest free tier quota!)
    GEMINI_FREE_RPM = 15  # Requests per minute
    GEMINI_FREE_RPD = 1000  # Requests per day (Gemini 2.5 Flash-Lite)
    GEMINI_FREE_TPM = 250_000  # Tokens per minute (250K)
    
    # Gemini Paid Tier 1 Limits (for reference)
    GEMINI_TIER1_RPM = 1000
    GEMINI_TIER1_RPD = 10000  # Much higher for paid tier
    
    # OpenAI Pricing (GPT-4o-mini)
    OPENAI_INPUT_COST_PER_1M = 0.15  # $0.15 per 1M input tokens
    OPENAI_OUTPUT_COST_PER_1M = 0.60  # $0.60 per 1M output tokens
    
    def __init__(self, storage_file: str = "data/llm_usage.json"):
        """Initialize usage tracker"""
        self.storage_file = Path(storage_file)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.stats = self._load_stats()
        self.lock = threading.Lock()
        
        # In-memory counters for rate limiting
        self.minute_requests = []  # List of (timestamp, provider) tuples
        self.daily_requests = []
        
        logger.info("✅ LLM Usage Tracker initialized")
    
    def _load_stats(self) -> UsageStats:
        """Load usage statistics from file"""
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    return UsageStats(**data)
            else:
                # Initialize with today's date
                return UsageStats(last_reset=datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Error loading usage stats: {e}")
            return UsageStats(last_reset=datetime.now().isoformat())
    
    def _save_stats(self):
        """Save usage statistics to file"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(asdict(self.stats), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving usage stats: {e}")
    
    def _check_daily_reset(self):
        """Reset daily counters if new day"""
        try:
            last_reset = datetime.fromisoformat(self.stats.last_reset)
            now = datetime.now()
            
            if now.date() > last_reset.date():
                logger.info("🔄 Resetting daily usage counters")
                self.stats.gemini_requests = 0
                self.stats.last_reset = now.isoformat()
                self.daily_requests.clear()
                self._save_stats()
        except Exception as e:
            logger.error(f"Error checking daily reset: {e}")
    
    def can_make_request(self, provider: str = "gemini") -> tuple[bool, Optional[str]]:
        """
        Check if request can be made without exceeding limits
        
        Returns:
            (can_proceed, warning_message)
        """
        with self.lock:
            self._check_daily_reset()
            
            if provider.lower() == "gemini":
                return self._check_gemini_limits()
            else:
                # OpenAI has no free tier, just track usage
                return True, None
    
    def _check_gemini_limits(self) -> tuple[bool, Optional[str]]:
        """Check Gemini free tier limits"""
        now = datetime.now()
        
        # Clean old entries (older than 1 minute)
        one_minute_ago = now - timedelta(minutes=1)
        self.minute_requests = [
            (ts, prov) for ts, prov in self.minute_requests 
            if ts > one_minute_ago and prov == "gemini"
        ]
        
        # Check RPM (Requests Per Minute)
        rpm_count = len(self.minute_requests)
        if rpm_count >= self.GEMINI_FREE_RPM:
            return False, f"⚠️ Gemini RPM limit reached ({rpm_count}/{self.GEMINI_FREE_RPM}). Wait 1 minute."
        
        # Check RPD (Requests Per Day)
        if self.stats.gemini_requests >= self.GEMINI_FREE_RPD:
            return False, f"❌ Gemini daily limit reached ({self.stats.gemini_requests}/{self.GEMINI_FREE_RPD}). Try tomorrow or switch accounts."
        
        # Warnings at 80% and 90%
        usage_percent = (self.stats.gemini_requests / self.GEMINI_FREE_RPD) * 100
        if usage_percent >= 90:
            return True, f"🔴 Critical: {usage_percent:.0f}% of daily quota used ({self.stats.gemini_requests}/{self.GEMINI_FREE_RPD})"
        elif usage_percent >= 80:
            return True, f"🟡 Warning: {usage_percent:.0f}% of daily quota used ({self.stats.gemini_requests}/{self.GEMINI_FREE_RPD})"
        elif usage_percent >= 50:
            return True, f"🟢 {usage_percent:.0f}% of daily quota used ({self.stats.gemini_requests}/{self.GEMINI_FREE_RPD})"
        
        return True, None
    
    def track_request(self, provider: str, success: bool, tokens_used: int = 0, 
                     input_tokens: int = 0, output_tokens: int = 0):
        """
        Track an LLM API request
        
        Args:
            provider: 'gemini' or 'openai'
            success: Whether request succeeded
            tokens_used: Total tokens (for Gemini)
            input_tokens: Input tokens (for OpenAI)
            output_tokens: Output tokens (for OpenAI)
        """
        with self.lock:
            self._check_daily_reset()
            
            now = datetime.now()
            provider = provider.lower()
            
            # Update counters
            self.stats.total_requests += 1
            if success:
                self.stats.successful_requests += 1
            else:
                self.stats.failed_requests += 1
            
            # Provider-specific tracking
            if provider == "gemini":
                self.stats.gemini_requests += 1
                self.stats.gemini_tokens += tokens_used
                self.stats.total_tokens_used += tokens_used
                self.minute_requests.append((now, "gemini"))
                self.daily_requests.append((now, "gemini"))
                
            elif provider == "openai":
                self.stats.openai_requests += 1
                total_tokens = input_tokens + output_tokens
                self.stats.openai_tokens += total_tokens
                self.stats.total_tokens_used += total_tokens
                
                # Calculate cost
                input_cost = (input_tokens / 1_000_000) * self.OPENAI_INPUT_COST_PER_1M
                output_cost = (output_tokens / 1_000_000) * self.OPENAI_OUTPUT_COST_PER_1M
                request_cost = input_cost + output_cost
                
                self.stats.openai_cost += request_cost
                self.stats.total_cost_usd += request_cost
                
                self.minute_requests.append((now, "openai"))
                self.daily_requests.append((now, "openai"))
            
            self._save_stats()
            
            logger.info(f"📊 Tracked {provider} request: success={success}, tokens={tokens_used or (input_tokens + output_tokens)}")
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current usage summary"""
        with self.lock:
            self._check_daily_reset()
            
            # Debug logging
            logger.info(f"📊 Usage Summary - Gemini requests: {self.stats.gemini_requests}, Total: {self.stats.total_requests}")
            
            # Calculate usage percentages
            gemini_daily_percent = (self.stats.gemini_requests / self.GEMINI_FREE_RPD) * 100
            
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
                "total_requests": self.stats.total_requests,
                "successful_requests": self.stats.successful_requests,
                "failed_requests": self.stats.failed_requests,
                "gemini": {
                    "requests_today": self.stats.gemini_requests,
                    "daily_limit": self.GEMINI_FREE_RPD,
                    "remaining": self.GEMINI_FREE_RPD - self.stats.gemini_requests,
                    "usage_percent": round(gemini_daily_percent, 1),
                    "tokens_used": self.stats.gemini_tokens
                },
                "openai": {
                    "requests_total": self.stats.openai_requests,
                    "tokens_used": self.stats.openai_tokens,
                    "cost_usd": round(self.stats.openai_cost, 4)
                },
                "total_cost_usd": round(self.stats.total_cost_usd, 4),
                "last_reset": self.stats.last_reset
            }
    
    def reset_stats(self):
        """Reset all statistics (admin function)"""
        with self.lock:
            self.stats = UsageStats(last_reset=datetime.now().isoformat())
            self.minute_requests.clear()
            self.daily_requests.clear()
            self._save_stats()
            logger.info("🔄 Usage statistics reset")


# Global tracker instance
_tracker_instance = None

def get_tracker() -> LLMUsageTracker:
    """Get global tracker instance"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = LLMUsageTracker()
    return _tracker_instance
