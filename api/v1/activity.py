"""
Activity Tracking API - Phase 3
================================
API endpoints for user activity tracking and analytics.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime
from typing import List, Optional

from core.database import get_db
from core.auth import get_current_user
from models.database import User
from services.activity_tracker import ActivityTracker

router = APIRouter()


@router.get("/activity/summary")
async def get_activity_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get activity summary for the current user.
    
    Returns aggregated activity metrics for the specified period.
    """
    # Handle both dict and object
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    
    tracker = ActivityTracker(db)
    summary = await tracker.get_user_activity_summary(user_id, days=days)
    
    return {
        "success": True,
        "data": summary
    }


@router.get("/activity/daily/{target_date}")
async def get_daily_stats(
    target_date: date,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get daily activity statistics for a specific date.
    """
    # Handle both dict and object
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    
    tracker = ActivityTracker(db)
    daily_stats = await tracker.aggregate_daily_stats(user_id, target_date)
    
    return {
        "success": True,
        "data": {
            "date": daily_stats.date.isoformat(),
            "logins": daily_stats.logins_count,
            "resumes_vetted": daily_stats.resumes_vetted,
            "candidates_viewed": daily_stats.candidates_viewed,
            "candidates_created": daily_stats.candidates_created,
            "searches": daily_stats.searches_performed,
            "jobs_created": daily_stats.jobs_created,
            "interviews_scheduled": daily_stats.interviews_scheduled,
            "total_actions": daily_stats.total_actions,
            "session_time_hours": daily_stats.total_session_time / 3600
        }
    }


@router.get("/admin/team-leaderboard")
async def get_team_leaderboard(
    period: str = Query("month", regex="^(day|week|month)$"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get team leaderboard (admin only).
    
    Shows top performers based on productivity scores.
    """
    # Check if user is admin (handle both dict and object)
    user_role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    tracker = ActivityTracker(db)
    leaderboard = await tracker.get_team_leaderboard(period=period, limit=limit)
    
    return {
        "success": True,
        "data": {
            "period": period,
            "leaderboard": leaderboard
        }
    }


@router.post("/admin/aggregate-stats")
async def trigger_stats_aggregation(
    target_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger stats aggregation for a specific date (admin only).
    
    Useful for backfilling or recalculating statistics.
    """
    # Check if user is admin (handle both dict and object)
    user_role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not target_date:
        target_date = date.today()
    
    tracker = ActivityTracker(db)
    
    # Aggregate for all users
    from sqlalchemy import select
    from models.database import User as UserModel
    
    result = await db.execute(select(UserModel))
    users = result.scalars().all()
    
    aggregated_count = 0
    for user in users:
        try:
            await tracker.aggregate_daily_stats(user.id, target_date)
            aggregated_count += 1
        except Exception as e:
            # Log error but continue with other users
            print(f"Error aggregating stats for user {user.id}: {e}")
    
    return {
        "success": True,
        "message": f"Aggregated stats for {aggregated_count} users on {target_date.isoformat()}"
    }
