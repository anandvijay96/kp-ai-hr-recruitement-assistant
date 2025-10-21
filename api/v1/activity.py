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


@router.get("/admin/team-activity-summary")
async def get_team_activity_summary(
    days: int = Query(1, ge=1, le=365, description="Number of days to look back"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get team-wide activity summary (admin only).
    
    Returns aggregated activity metrics for ALL users in the specified period.
    """
    # Check if user is admin (handle both dict and object)
    user_role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    tracker = ActivityTracker(db)
    summary = await tracker.get_team_activity_summary(days=days)
    
    return {
        "success": True,
        "data": summary
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


@router.get("/admin/activity-trend")
async def get_activity_trend(
    days: int = Query(7, ge=1, le=30, description="Number of days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get daily activity trend for the last N days (admin only).
    Returns data for line chart.
    """
    # Check if user is admin
    user_role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    tracker = ActivityTracker(db)
    trend_data = await tracker.get_activity_trend(days=days)
    
    return {
        "success": True,
        "data": trend_data
    }


@router.get("/admin/activity-distribution")
async def get_activity_distribution(
    days: int = Query(7, ge=1, le=365, description="Number of days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get activity distribution by type (admin only).
    Returns data for pie/doughnut chart.
    """
    # Check if user is admin
    user_role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    tracker = ActivityTracker(db)
    distribution = await tracker.get_activity_distribution(days=days)
    
    return {
        "success": True,
        "data": distribution
    }


@router.get("/admin/recent-activity")
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50, description="Number of activities"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent activity feed (admin only).
    Returns latest user activities across the system.
    """
    # Check if user is admin
    user_role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    tracker = ActivityTracker(db)
    activities = await tracker.get_recent_activity(limit=limit)
    
    return {
        "success": True,
        "data": activities
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


@router.get("/admin/activity-stats")
async def get_activity_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall activity statistics (admin only).
    Returns counts for today, this week, and this month.
    """
    # Check if user is admin
    user_role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from sqlalchemy import select, func, and_
    from models.database import UserActivityLog
    from datetime import timedelta
    
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = datetime(now.year, now.month, 1)
    
    # Count today's activities
    result = await db.execute(
        select(func.count(UserActivityLog.id)).where(
            UserActivityLog.timestamp >= today_start
        )
    )
    today_count = result.scalar() or 0
    
    # Count this week's activities
    result = await db.execute(
        select(func.count(UserActivityLog.id)).where(
            UserActivityLog.timestamp >= week_start
        )
    )
    week_count = result.scalar() or 0
    
    # Count this month's activities
    result = await db.execute(
        select(func.count(UserActivityLog.id)).where(
            UserActivityLog.timestamp >= month_start
        )
    )
    month_count = result.scalar() or 0
    
    # Count active users today
    result = await db.execute(
        select(func.count(func.distinct(UserActivityLog.user_id))).where(
            UserActivityLog.timestamp >= today_start
        )
    )
    active_users = result.scalar() or 0
    
    return {
        "success": True,
        "stats": {
            "today": today_count,
            "this_week": week_count,
            "this_month": month_count,
            "active_users_today": active_users
        }
    }


@router.get("/admin/activity-logs")
async def get_activity_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: Optional[str] = None,
    action_type: Optional[str] = None,
    date_range: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated activity logs with filters (admin only).
    """
    # Check if user is admin
    user_role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from sqlalchemy import select, and_, func
    from models.database import UserActivityLog, User as UserModel
    from datetime import timedelta
    
    # Build query
    query = select(UserActivityLog).join(
        UserModel, UserActivityLog.user_id == UserModel.id, isouter=True
    )
    
    # Apply filters
    conditions = []
    
    if user_id:
        conditions.append(UserActivityLog.user_id == user_id)
    
    if action_type:
        conditions.append(UserActivityLog.action_type == action_type)
    
    if date_range:
        now = datetime.now()
        if date_range == "today":
            start = datetime(now.year, now.month, now.day)
            conditions.append(UserActivityLog.timestamp >= start)
        elif date_range == "yesterday":
            yesterday = now - timedelta(days=1)
            start = datetime(yesterday.year, yesterday.month, yesterday.day)
            end = datetime(now.year, now.month, now.day)
            conditions.append(and_(
                UserActivityLog.timestamp >= start,
                UserActivityLog.timestamp < end
            ))
        elif date_range == "week":
            start = now - timedelta(days=now.weekday())
            start = datetime(start.year, start.month, start.day)
            conditions.append(UserActivityLog.timestamp >= start)
        elif date_range == "month":
            start = datetime(now.year, now.month, 1)
            conditions.append(UserActivityLog.timestamp >= start)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Order by timestamp descending
    query = query.order_by(UserActivityLog.timestamp.desc())
    
    # Count total
    count_query = select(func.count()).select_from(UserActivityLog)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    result = await db.execute(count_query)
    total = result.scalar() or 0
    
    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Format logs
    formatted_logs = []
    for log in logs:
        # Get user info
        user_result = await db.execute(
            select(UserModel).where(UserModel.id == log.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        formatted_logs.append({
            "id": log.id,
            "user_id": log.user_id,
            "user_name": user.full_name if user else "Unknown",
            "action_type": log.action_type,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "request_method": log.request_method,
            "request_path": log.request_path,
            "duration_ms": log.duration_ms,
            "status": log.status,
            "error_message": log.error_message,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        })
    
    return {
        "success": True,
        "logs": formatted_logs,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


@router.get("/admin/activity-logs/export")
async def export_activity_logs(
    user_id: Optional[str] = None,
    action_type: Optional[str] = None,
    date_range: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export activity logs to CSV (admin only).
    """
    # Check if user is admin
    user_role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from fastapi.responses import StreamingResponse
    from sqlalchemy import select, and_
    from models.database import UserActivityLog, User as UserModel
    from datetime import timedelta
    import io
    import csv
    
    # Build query (same as get_activity_logs)
    query = select(UserActivityLog).join(
        UserModel, UserActivityLog.user_id == UserModel.id, isouter=True
    )
    
    conditions = []
    if user_id:
        conditions.append(UserActivityLog.user_id == user_id)
    if action_type:
        conditions.append(UserActivityLog.action_type == action_type)
    if date_range:
        now = datetime.now()
        if date_range == "today":
            start = datetime(now.year, now.month, now.day)
            conditions.append(UserActivityLog.timestamp >= start)
        elif date_range == "week":
            start = now - timedelta(days=now.weekday())
            start = datetime(start.year, start.month, start.day)
            conditions.append(UserActivityLog.timestamp >= start)
        elif date_range == "month":
            start = datetime(now.year, now.month, 1)
            conditions.append(UserActivityLog.timestamp >= start)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(UserActivityLog.timestamp.desc())
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Timestamp', 'User', 'Action Type', 'Entity Type', 'Entity ID',
        'IP Address', 'Request Method', 'Request Path', 'Duration (ms)', 'Status'
    ])
    
    # Data
    for log in logs:
        user_result = await db.execute(
            select(UserModel).where(UserModel.id == log.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        writer.writerow([
            log.timestamp.isoformat() if log.timestamp else '',
            user.full_name if user else 'Unknown',
            log.action_type or '',
            log.entity_type or '',
            log.entity_id or '',
            log.ip_address or '',
            log.request_method or '',
            log.request_path or '',
            log.duration_ms or '',
            log.status or ''
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=activity_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )
