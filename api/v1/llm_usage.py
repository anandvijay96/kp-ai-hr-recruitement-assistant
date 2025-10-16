"""
LLM Usage API - Monitor and manage LLM API usage
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from services.llm_usage_tracker import get_tracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm-usage", tags=["LLM Usage"])


@router.get("/stats")
async def get_usage_stats() -> Dict[str, Any]:
    """
    Get current LLM usage statistics
    
    Returns:
        Usage statistics including quota limits and warnings
    """
    try:
        tracker = get_tracker()
        stats = tracker.get_usage_summary()
        return stats
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_usage_stats() -> Dict[str, str]:
    """
    Reset usage statistics (admin only)
    
    Returns:
        Success message
    """
    try:
        tracker = get_tracker()
        tracker.reset_stats()
        return {"message": "Usage statistics reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting usage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-quota/{provider}")
async def check_quota(provider: str) -> Dict[str, Any]:
    """
    Check if quota allows making a request
    
    Args:
        provider: 'gemini' or 'openai'
    
    Returns:
        can_proceed, warning_message
    """
    try:
        tracker = get_tracker()
        can_proceed, warning = tracker.can_make_request(provider)
        
        return {
            "can_proceed": can_proceed,
            "warning": warning,
            "provider": provider
        }
    except Exception as e:
        logger.error(f"Error checking quota: {e}")
        raise HTTPException(status_code=500, detail=str(e))
