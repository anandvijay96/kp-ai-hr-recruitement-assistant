"""
Jobs Analytics API
Provides real-time analytics data for the jobs management dashboard
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import logging

from core.database import get_db
from models.database import Job, Resume, ResumeJobMatch
from core.auth import get_current_user_or_redirect

router = APIRouter(prefix="/jobs-management", tags=["jobs-analytics"])
logger = logging.getLogger(__name__)


@router.get("/analytics")
async def get_analytics_data(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive analytics data for jobs dashboard
    
    Returns:
        - stats: Overall statistics
        - timeline: Jobs posted over time
        - statusBreakdown: Jobs by status
        - departmentBreakdown: Jobs by department
        - topJobs: Top performing jobs
        - recentActivity: Recent job activities
    """
    try:
        # Get overall stats
        stats = await get_overall_stats(db)
        
        # Get timeline data (last 30 days)
        timeline = await get_jobs_timeline(db)
        
        # Get status breakdown
        status_breakdown = await get_status_breakdown(db)
        
        # Get department breakdown
        department_breakdown = await get_department_breakdown(db)
        
        # Get top performing jobs
        top_jobs = await get_top_jobs(db)
        
        # Get recent activity
        recent_activity = await get_recent_activity(db)
        
        return {
            "stats": stats,
            "timeline": timeline,
            "statusBreakdown": status_breakdown,
            "departmentBreakdown": department_breakdown,
            "topJobs": top_jobs,
            "recentActivity": recent_activity
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load analytics data")


async def get_overall_stats(db: AsyncSession) -> Dict[str, Any]:
    """Get overall statistics"""
    
    # Total jobs
    total_jobs_stmt = select(func.count(Job.id))
    total_jobs_result = await db.execute(total_jobs_stmt)
    total_jobs = total_jobs_result.scalar() or 0
    
    # Open jobs
    open_jobs_stmt = select(func.count(Job.id)).where(Job.status == 'open')
    open_jobs_result = await db.execute(open_jobs_stmt)
    open_jobs = open_jobs_result.scalar() or 0
    
    # Total applications (count of resume-job matches)
    total_apps_stmt = select(func.count(ResumeJobMatch.id))
    total_apps_result = await db.execute(total_apps_stmt)
    total_applications = total_apps_result.scalar() or 0
    
    # Average match score
    avg_match_stmt = select(func.avg(ResumeJobMatch.match_score))
    avg_match_result = await db.execute(avg_match_stmt)
    avg_match_score = avg_match_result.scalar() or 0
    avg_match_score = round(avg_match_score, 1) if avg_match_score else 0
    
    # Jobs growth (compare with last month)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    sixty_days_ago = datetime.now() - timedelta(days=60)
    
    current_month_stmt = select(func.count(Job.id)).where(Job.created_at >= thirty_days_ago)
    current_month_result = await db.execute(current_month_stmt)
    current_month_jobs = current_month_result.scalar() or 0
    
    prev_month_stmt = select(func.count(Job.id)).where(
        and_(Job.created_at >= sixty_days_ago, Job.created_at < thirty_days_ago)
    )
    prev_month_result = await db.execute(prev_month_stmt)
    prev_month_jobs = prev_month_result.scalar() or 1  # Avoid division by zero
    
    jobs_growth = round(((current_month_jobs - prev_month_jobs) / prev_month_jobs) * 100, 1) if prev_month_jobs > 0 else 0
    
    return {
        "totalJobs": total_jobs,
        "openJobs": open_jobs,
        "totalApplications": total_applications,
        "avgMatchScore": avg_match_score,
        "jobsGrowth": jobs_growth
    }


async def get_jobs_timeline(db: AsyncSession, days: int = 30) -> Dict[str, List]:
    """Get jobs posted over time"""
    
    # Get jobs from last N days
    start_date = datetime.now() - timedelta(days=days)
    
    stmt = select(
        func.date(Job.created_at).label('date'),
        func.count(Job.id).label('count')
    ).where(
        Job.created_at >= start_date
    ).group_by(
        func.date(Job.created_at)
    ).order_by(
        func.date(Job.created_at)
    )
    
    result = await db.execute(stmt)
    data = result.all()
    
    # Create labels and values
    labels = []
    values = []
    
    for row in data:
        # Handle both date objects and strings
        if isinstance(row.date, str):
            # Parse string date
            date_obj = datetime.strptime(row.date, '%Y-%m-%d').date()
            labels.append(date_obj.strftime('%b %d'))
        else:
            labels.append(row.date.strftime('%b %d'))
        values.append(row.count)
    
    return {
        "labels": labels,
        "values": values
    }


async def get_status_breakdown(db: AsyncSession) -> Dict[str, List]:
    """Get jobs by status"""
    
    stmt = select(
        Job.status,
        func.count(Job.id).label('count')
    ).group_by(Job.status)
    
    result = await db.execute(stmt)
    data = result.all()
    
    # Map status to labels
    status_map = {
        'open': 'Open',
        'closed': 'Closed',
        'on_hold': 'On Hold',
        'draft': 'Draft',
        'archived': 'Archived'
    }
    
    labels = []
    values = []
    
    for row in data:
        labels.append(status_map.get(row.status, row.status.title()))
        values.append(row.count)
    
    return {
        "labels": labels,
        "values": values
    }


async def get_department_breakdown(db: AsyncSession) -> Dict[str, List]:
    """Get jobs by department"""
    
    stmt = select(
        Job.department,
        func.count(Job.id).label('count')
    ).where(
        Job.department.isnot(None)
    ).group_by(
        Job.department
    ).order_by(
        desc('count')
    ).limit(10)
    
    result = await db.execute(stmt)
    data = result.all()
    
    labels = []
    values = []
    
    for row in data:
        labels.append(row.department or 'Unknown')
        values.append(row.count)
    
    return {
        "labels": labels,
        "values": values
    }


async def get_top_jobs(db: AsyncSession, limit: int = 5) -> List[Dict]:
    """Get top performing jobs by application count"""
    
    stmt = select(
        Job.id,
        Job.title,
        Job.department,
        func.count(ResumeJobMatch.id).label('application_count'),
        func.avg(ResumeJobMatch.match_score).label('avg_match_score')
    ).outerjoin(
        ResumeJobMatch, Job.id == ResumeJobMatch.job_id
    ).where(
        Job.status == 'open'
    ).group_by(
        Job.id, Job.title, Job.department
    ).order_by(
        desc('application_count')
    ).limit(limit)
    
    result = await db.execute(stmt)
    data = result.all()
    
    jobs = []
    for row in data:
        jobs.append({
            "id": row.id,
            "title": row.title,
            "department": row.department,
            "applicationCount": row.application_count or 0,
            "avgMatchScore": round(row.avg_match_score, 1) if row.avg_match_score else 0
        })
    
    return jobs


async def get_recent_activity(db: AsyncSession, limit: int = 10) -> List[Dict]:
    """Get recent job activities"""
    
    # Get recently created jobs
    stmt = select(Job).order_by(desc(Job.created_at)).limit(limit)
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    
    activities = []
    for job in jobs:
        # Make job.created_at timezone-aware if it's naive
        job_created_at = job.created_at
        if job_created_at.tzinfo is None:
            # If naive, assume UTC
            job_created_at = job_created_at.replace(tzinfo=timezone.utc)
        
        time_diff = datetime.now(timezone.utc) - job_created_at
        
        if time_diff.days > 0:
            time_ago = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
        elif time_diff.seconds // 3600 > 0:
            hours = time_diff.seconds // 3600
            time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            minutes = time_diff.seconds // 60
            time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        
        activities.append({
            "action": "Job Posted",
            "description": f"{job.title} in {job.department or 'Unknown'} department",
            "timeAgo": time_ago
        })
    
    return activities
