"""
LLM Usage API - Monitor and manage LLM API usage
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import os
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


@router.get("/available-providers")
async def get_available_providers() -> Dict[str, Any]:
    """
    Check which LLM providers are available based on API keys
    
    Returns:
        Dictionary with provider availability
    """
    try:
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        return {
            "gemini": {
                "available": bool(gemini_key and gemini_key.strip()),
                "name": "Gemini 2.0 Flash (Free)",
                "icon": "google",
                "limits": {
                    "rpm": 15,
                    "rpd": 50,  # Updated: 50 requests/day for free tier
                    "tpm": 1000000
                },
                "warning": "⚠️ Free tier: 50 requests/day limit"
            },
            "openai": {
                "available": bool(openai_key and openai_key.strip()),
                "name": "OpenAI GPT-4o-mini (Paid)",
                "icon": "stars",
                "limits": {
                    "rpm": 500,
                    "rpd": 10000,
                    "tpm": 200000
                },
                "warning": None
            }
        }
    except Exception as e:
        logger.error(f"Error checking available providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))
