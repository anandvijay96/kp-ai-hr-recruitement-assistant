"""
Vetting Queue API Endpoints
============================
API endpoints for managing vetting queue and rate limiting.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

from core.database import get_db
from core.auth import get_current_user
from models.database import User
from services.vetting_queue import vetting_queue

router = APIRouter()


@router.get("/vetting-queue/status")
async def get_queue_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current vetting queue status.
    
    Returns:
    - Active session info
    - Queue length
    - User's position in queue (if applicable)
    - Rate limit status
    """
    # Get user info
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    user_name = current_user.get("full_name") if isinstance(current_user, dict) else current_user.full_name
    
    # Get queue status
    queue_status = vetting_queue.get_queue_status()
    
    # Get user's position
    user_position = vetting_queue.get_queue_position(user_id)
    
    # Get rate limit status
    rate_limit = vetting_queue.get_rate_limit_status()
    
    # Check if user has active session
    active_session = queue_status["active_session"]
    user_is_active = active_session and active_session["user_id"] == user_id
    
    return {
        "success": True,
        "data": {
            "active_session": active_session,
            "queue_length": queue_status["queue_length"],
            "is_available": queue_status["is_available"],
            "user_position": user_position,
            "user_is_active": user_is_active,
            "user_is_in_queue": user_position > 0,
            "rate_limit": rate_limit
        }
    }


@router.post("/vetting-queue/join")
async def join_queue(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Join the vetting queue.
    
    If no one is vetting, session starts immediately.
    Otherwise, user is added to queue.
    """
    # Get user info
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    user_name = current_user.get("full_name") if isinstance(current_user, dict) else current_user.full_name
    
    # Join queue
    result = await vetting_queue.join_queue(user_id, user_name)
    
    return {
        "success": result["success"],
        "message": result["message"],
        "data": result
    }


@router.post("/vetting-queue/leave")
async def leave_queue(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Leave the vetting queue.
    """
    # Get user info
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    
    # Leave queue
    result = vetting_queue.leave_queue(user_id)
    
    return {
        "success": result["success"],
        "message": result["message"]
    }


@router.post("/vetting-queue/start-session")
async def start_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a vetting session.
    
    Only works if:
    1. No one else is vetting
    2. Rate limit not exceeded
    """
    # Get user info
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    user_name = current_user.get("full_name") if isinstance(current_user, dict) else current_user.full_name
    
    # Start session
    result = await vetting_queue.start_vetting_session(user_id, user_name)
    
    return {
        "success": result["success"],
        "message": result["message"],
        "data": result
    }


@router.post("/vetting-queue/end-session")
async def end_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    End current vetting session.
    
    Automatically processes next user in queue.
    """
    # Get user info
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    
    # End session
    result = vetting_queue.end_vetting_session(user_id)
    
    return {
        "success": result["success"],
        "message": result["message"]
    }


@router.post("/vetting-queue/increment-rate-limit")
async def increment_rate_limit(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Increment rate limit counter (called after each Gemini API request).
    
    Internal endpoint used by vetting service.
    """
    vetting_queue.increment_rate_limit()
    
    rate_limit = vetting_queue.get_rate_limit_status()
    
    return {
        "success": True,
        "data": rate_limit
    }


@router.get("/vetting-queue/rate-limit")
async def get_rate_limit(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current rate limit status.
    """
    rate_limit = vetting_queue.get_rate_limit_status()
    
    return {
        "success": True,
        "data": rate_limit
    }
