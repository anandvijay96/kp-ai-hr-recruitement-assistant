import hashlib
import json
import logging
from typing import Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SimpleCache:
    """Simple in-memory cache for analysis results"""

    def __init__(self, ttl_minutes: int = 60):
        """
        Initialize cache
        
        Args:
            ttl_minutes: Time to live for cache entries in minutes
        """
        self._cache = {}
        self._ttl = timedelta(minutes=ttl_minutes)

    def _generate_key(self, file_content: bytes, jd_text: Optional[str] = None) -> str:
        """Generate cache key from file content and JD"""
        hasher = hashlib.md5()
        hasher.update(file_content)
        if jd_text:
            hasher.update(jd_text.encode('utf-8'))
        return hasher.hexdigest()

    def get(self, file_content: bytes, jd_text: Optional[str] = None) -> Optional[Any]:
        """
        Get cached result
        
        Args:
            file_content: File content bytes
            jd_text: Optional job description text
            
        Returns:
            Cached result or None if not found/expired
        """
        try:
            key = self._generate_key(file_content, jd_text)
            
            if key in self._cache:
                entry = self._cache[key]
                
                # Check if entry is expired
                if datetime.utcnow() - entry['timestamp'] < self._ttl:
                    logger.info(f"Cache hit for key: {key[:8]}...")
                    return entry['data']
                else:
                    # Remove expired entry
                    del self._cache[key]
                    logger.info(f"Cache expired for key: {key[:8]}...")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return None

    def set(self, file_content: bytes, data: Any, jd_text: Optional[str] = None):
        """
        Set cache entry
        
        Args:
            file_content: File content bytes
            data: Data to cache
            jd_text: Optional job description text
        """
        try:
            key = self._generate_key(file_content, jd_text)
            
            self._cache[key] = {
                'data': data,
                'timestamp': datetime.utcnow()
            }
            
            logger.info(f"Cached result for key: {key[:8]}...")
            
            # Clean up old entries if cache is getting large
            if len(self._cache) > 100:
                self._cleanup()
                
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")

    def _cleanup(self):
        """Remove expired entries from cache"""
        try:
            current_time = datetime.utcnow()
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time - entry['timestamp'] >= self._ttl
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
        except Exception as e:
            logger.error(f"Error cleaning up cache: {str(e)}")

    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            'total_entries': len(self._cache),
            'ttl_minutes': self._ttl.total_seconds() / 60
        }
