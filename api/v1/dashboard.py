"""
Dashboard API endpoints
Provides data for role-based dashboards
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta
from typing import Dict, List, Any

from core.database import get_db
from models.database import Resume
from models.database import Candidate
# from models.job import Job  # Uncomment when Job model is available
# from models.user import User  # Uncomment when User model is available

router = APIRouter()


@router.get("/dashboard/hr")
async def get_hr_dashboard_data(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get HR dashboard data
    Returns stats, pending vetting, recent candidates, active jobs, and recent activity
    """
    try:
        # Get quick stats
        stats = await get_hr_stats(db)
        
        # Get pending vetting resumes
        pending_vetting = await get_pending_vetting(db)
        
        # Get recent candidates
        recent_candidates = await get_recent_candidates(db)
        
        # Get active jobs (mock data for now until Job model is available)
        active_jobs = await get_active_jobs(db)
        
        # Get recent activity
        recent_activity = await get_recent_activity(db)
        
        return {
            "stats": stats,
            "pending_vetting": pending_vetting,
            "recent_candidates": recent_candidates,
            "active_jobs": active_jobs,
            "recent_activity": recent_activity
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")


async def get_hr_stats(db: AsyncSession) -> Dict[str, int]:
    """Get quick stats for HR dashboard"""
    
    # Total candidates
    total_candidates_query = select(func.count(Candidate.id))
    total_candidates_result = await db.execute(total_candidates_query)
    total_candidates = total_candidates_result.scalar() or 0
    
    # Pending vetting (resumes not yet vetted)
    pending_vetting_query = select(func.count(Resume.id)).where(
        Resume.authenticity_score == None
    )
    pending_vetting_result = await db.execute(pending_vetting_query)
    pending_vetting = pending_vetting_result.scalar() or 0
    
    # Shortlisted candidates (using 'screened' status from Candidate model)
    shortlisted_query = select(func.count(Candidate.id)).where(
        Candidate.status == "screened"  # Changed from "shortlisted" to match model constraint
    )
    shortlisted_result = await db.execute(shortlisted_query)
    shortlisted = shortlisted_result.scalar() or 0
    
    # Active jobs (mock for now)
    active_jobs = 8  # TODO: Replace with actual query when Job model is available
    
    return {
        "total_candidates": total_candidates,
        "pending_vetting": pending_vetting,
        "shortlisted": shortlisted,
        "active_jobs": active_jobs
    }


async def get_pending_vetting(db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
    """Get resumes pending vetting"""
    
    query = select(Resume).where(
        Resume.authenticity_score == None
    ).order_by(desc(Resume.upload_date)).limit(limit)
    
    result = await db.execute(query)
    resumes = result.scalars().all()
    
    return [
        {
            "id": resume.id,
            "name": resume.candidate_name or "Unknown Candidate",
            "uploaded_at": resume.upload_date.isoformat() if resume.upload_date else None,
            "position": None,  # Resume model doesn't have position field
            "file_name": resume.file_name
        }
        for resume in resumes
    ]


async def get_recent_candidates(db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recently added candidates"""
    
    query = select(Candidate).order_by(desc(Candidate.created_at)).limit(limit)
    
    result = await db.execute(query)
    candidates = result.scalars().all()
    
    return [
        {
            "id": candidate.id,
            "name": candidate.full_name,  # Changed from candidate.name
            "score": None,  # Candidate model doesn't have overall_score field yet
            "status": candidate.status or "new",
            "position": None,  # Candidate model doesn't have position field
            "created_at": candidate.created_at.isoformat() if candidate.created_at else None
        }
        for candidate in candidates
    ]


async def get_active_jobs(db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get active jobs
    TODO: Replace with actual query when Job model is available
    """
    
    # Mock data for now
    return [
        {
            "id": 1,
            "title": "Senior Java Developer",
            "candidate_count": 24,
            "days_open": 15,
            "department": "Engineering",
            "status": "Active",
            "priority": "High"
        },
        {
            "id": 2,
            "title": "UI/UX Designer",
            "candidate_count": 18,
            "days_open": 8,
            "department": "Design",
            "status": "Active",
            "priority": "Medium"
        },
        {
            "id": 3,
            "title": "Data Analyst",
            "candidate_count": 12,
            "days_open": 22,
            "department": "Analytics",
            "status": "Active",
            "priority": "Low"
        }
    ]
    
    # Uncomment when Job model is available:
    # query = select(Job).where(
    #     Job.status == "active"
    # ).order_by(desc(Job.created_at)).limit(limit)
    # 
    # result = await db.execute(query)
    # jobs = result.scalars().all()
    # 
    # return [
    #     {
    #         "id": job.id,
    #         "title": job.title,
    #         "candidate_count": len(job.candidates) if hasattr(job, 'candidates') else 0,
    #         "days_open": (datetime.now() - job.created_at).days if job.created_at else 0,
    #         "department": job.department,
    #         "status": job.status,
    #         "priority": job.priority
    #     }
    #     for job in jobs
    # ]


async def get_recent_activity(db: AsyncSession, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get recent activity feed
    Combines recent uploads, vetting, and status changes
    """
    
    activities = []
    
    # Recent uploads
    recent_uploads_query = select(Resume).order_by(desc(Resume.upload_date)).limit(10)
    recent_uploads_result = await db.execute(recent_uploads_query)
    recent_uploads = recent_uploads_result.scalars().all()
    
    for resume in recent_uploads:
        activities.append({
            "type": "upload",
            "description": f"New resume uploaded: {resume.candidate_name or 'Unknown'}",
            "timestamp": resume.upload_date.isoformat() if resume.upload_date else None
        })
    
    # Recent vetting completions
    recent_vetted_query = select(Resume).where(
        Resume.authenticity_score != None
    ).order_by(desc(Resume.updated_at)).limit(10)
    recent_vetted_result = await db.execute(recent_vetted_query)
    recent_vetted = recent_vetted_result.scalars().all()
    
    for resume in recent_vetted:
        activities.append({
            "type": "vet",
            "description": f"Resume vetted: {resume.candidate_name or 'Unknown'} (Score: {resume.authenticity_score}%)",
            "timestamp": resume.updated_at.isoformat() if resume.updated_at else None
        })
    
    # Recent candidate status changes (using valid statuses from model)
    recent_candidates_query = select(Candidate).where(
        Candidate.status.in_(["screened", "interviewed", "offered", "hired"])  # Updated to match model constraints
    ).order_by(desc(Candidate.updated_at)).limit(10)
    recent_candidates_result = await db.execute(recent_candidates_query)
    recent_candidates = recent_candidates_result.scalars().all()
    
    for candidate in recent_candidates:
        activities.append({
            "type": candidate.status,
            "description": f"{candidate.full_name} moved to {candidate.status}",  # Changed from candidate.name
            "timestamp": candidate.updated_at.isoformat() if candidate.updated_at else None
        })
    
    # Sort by timestamp and limit
    activities.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    
    return activities[:limit]


@router.get("/dashboard/admin")
async def get_admin_dashboard_data(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get admin dashboard data
    Returns system stats, user activity, and performance metrics
    """
    
    # TODO: Implement admin dashboard data
    # This will include:
    # - Total users, jobs, resumes, vetted resumes
    # - User activity in last 24h
    # - System health metrics
    # - Performance metrics
    
    return {
        "stats": {
            "total_users": 45,
            "total_jobs": 23,
            "total_resumes": 1245,
            "vetted_resumes": 892,
            "today_uploads": 12
        },
        "user_activity": {},
        "system_health": {},
        "recent_users": [],
        "performance_metrics": {}
    }
