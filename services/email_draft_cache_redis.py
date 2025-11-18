"""Redis-based cache for recent email drafts per HR user and client.

This is a lightweight helper around the existing Redis instance used for
LLM usage tracking. We key drafts by user id + client + requirement/job,
with a short TTL so that HR can quickly re-open or regenerate recent
email drafts without re-running the full LLM flow.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import redis

from core.config import settings

logger = logging.getLogger(__name__)


class EmailDraftCacheRedis:
    """Cache recent email drafts in Redis.

    Keys are namespaced by user + client + requirement/job so that drafts
    are scoped per HR user and per requirement.
    """

    def __init__(self, redis_url: Optional[str] = None, ttl_hours: int = 12) -> None:
        self.redis_url = redis_url or settings.redis_url
        self.ttl_seconds = int(timedelta(hours=ttl_hours).total_seconds())
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            # Simple health check
            self.redis_client.ping()
            logger.info("✅ EmailDraftCacheRedis connected successfully")
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("❌ Failed to connect to Redis for email draft cache: %s", exc)
            logger.error("   Redis URL: %s", self.redis_url)
            raise

    def _slug(self, value: Optional[str], fallback: str) -> str:
        """Normalize a value into a safe slug fragment for Redis keys."""

        if not value or not str(value).strip():
            value = fallback
        value = str(value).strip().lower()
        # Replace non-alphanumeric with dashes
        value = re.sub(r"[^a-z0-9]+", "-", value)
        value = value.strip("-")
        # Avoid very long keys
        return value[:64] or fallback

    def _build_key(
        self,
        *,
        user_id: str,
        client_name: str,
        requirement_title: Optional[str],
        job_code: Optional[str],
    ) -> str:
        client_slug = self._slug(client_name, "client")
        requirement_source = requirement_title or job_code or "general"
        requirement_slug = self._slug(requirement_source, "req")
        return f"email_draft:{user_id}:{client_slug}:{requirement_slug}"

    def save_draft(
        self,
        *,
        user_id: str,
        client_name: str,
        requirement_title: Optional[str],
        job_code: Optional[str],
        draft_data: Dict[str, Any],
    ) -> None:
        """Save the latest draft for this user+client+requirement.

        The payload is stored as JSON with a small metadata wrapper so
        that we can extend it later if needed.
        """

        try:
            key = self._build_key(
                user_id=user_id,
                client_name=client_name,
                requirement_title=requirement_title,
                job_code=job_code,
            )
            payload = {
                "draft": draft_data,
                "updated_at": datetime.utcnow().isoformat(),
            }
            self.redis_client.setex(key, self.ttl_seconds, json.dumps(payload))
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to cache email draft for user %s: %s", user_id, exc)

    def get_draft(
        self,
        *,
        user_id: str,
        client_name: str,
        requirement_title: Optional[str],
        job_code: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Fetch the most recent draft for this user+client+requirement.

        Returns the raw draft payload that matches the EmailDraftResponse
        structure, or None if the cache entry is missing/invalid.
        """

        try:
            key = self._build_key(
                user_id=user_id,
                client_name=client_name,
                requirement_title=requirement_title,
                job_code=job_code,
            )
            raw = self.redis_client.get(key)
            if not raw:
                return None

            data = json.loads(raw)
            if isinstance(data, dict) and "draft" in data:
                draft = data["draft"]
            else:
                draft = data

            if not isinstance(draft, dict):
                logger.warning("Cached email draft at %s is not a dict; ignoring", key)
                return None

            return draft
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to read cached email draft for user %s: %s", user_id, exc)
            return None


_email_draft_cache_instance: Optional[EmailDraftCacheRedis] = None


def get_email_draft_cache() -> EmailDraftCacheRedis:
    """Get the global email draft cache instance."""

    global _email_draft_cache_instance
    if _email_draft_cache_instance is None:
        _email_draft_cache_instance = EmailDraftCacheRedis()
    return _email_draft_cache_instance
