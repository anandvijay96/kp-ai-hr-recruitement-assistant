"""
Interview Scheduling API - Phase 3 Day 5
=========================================
API endpoints for interview scheduling and management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from core.database import get_db
from core.auth import get_current_user
from services.interview_scheduler import InterviewScheduler

router = APIRouter()


class ScheduleInterviewRequest(BaseModel):
    candidate_id: str
    job_id: Optional[str] = None  # Optional since not all candidates have applied to jobs
    scheduled_datetime: datetime
    interview_type: str
    duration_minutes: int = 60
    interviewer_ids: Optional[List[str]] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    notes: Optional[str] = None
    interview_round: int = 1


class RescheduleRequest(BaseModel):
    new_datetime: datetime
    reason: Optional[str] = None


class CompleteInterviewRequest(BaseModel):
    rating: Optional[int] = None
    feedback: Optional[str] = None
    recommendation: Optional[str] = None
    notes: Optional[str] = None


@router.post("/interviews")
async def schedule_interview(
    request: ScheduleInterviewRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Schedule a new interview."""
    scheduler = InterviewScheduler(db)
    
    try:
        interview = await scheduler.schedule_interview(
            candidate_id=request.candidate_id,
            job_id=request.job_id,
            scheduled_by_user_id=current_user["id"],
            scheduled_datetime=request.scheduled_datetime,
            interview_type=request.interview_type,
            duration_minutes=request.duration_minutes,
            interviewer_ids=request.interviewer_ids,
            location=request.location,
            meeting_link=request.meeting_link,
            notes=request.notes,
            interview_round=request.interview_round
        )
        
        return {
            "success": True,
            "message": "Interview scheduled successfully",
            "interview_id": interview.id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/interviews/upcoming")
async def get_upcoming_interviews(
    days_ahead: int = 7,
    interviewer_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get upcoming interviews."""
    scheduler = InterviewScheduler(db)
    
    interviews = await scheduler.get_upcoming_interviews(
        days_ahead=days_ahead,
        interviewer_id=interviewer_id
    )
    
    return {
        "success": True,
        "data": [
            {
                "id": i.id,
                "candidate_id": i.candidate_id,
                "job_id": i.job_id,
                "scheduled_datetime": i.scheduled_datetime.isoformat(),
                "interview_type": i.interview_type,
                "duration_minutes": i.duration_minutes,
                "status": i.status,
                "location": i.location,
                "meeting_link": i.meeting_link
            }
            for i in interviews
        ]
    }


@router.get("/candidates/{candidate_id}/interviews")
async def get_candidate_interviews(
    candidate_id: str,
    include_cancelled: bool = False,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all interviews for a candidate."""
    scheduler = InterviewScheduler(db)
    
    interviews = await scheduler.get_candidate_interviews(
        candidate_id=candidate_id,
        include_cancelled=include_cancelled
    )
    
    return {
        "success": True,
        "data": [
            {
                "id": i.id,
                "scheduled_datetime": i.scheduled_datetime.isoformat(),
                "interview_type": i.interview_type,
                "status": i.status,
                "rating": i.rating,
                "recommendation": i.recommendation
            }
            for i in interviews
        ]
    }


@router.put("/interviews/{interview_id}/reschedule")
async def reschedule_interview(
    interview_id: str,
    request: RescheduleRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reschedule an interview."""
    scheduler = InterviewScheduler(db)
    
    try:
        interview = await scheduler.reschedule_interview(
            interview_id=interview_id,
            new_datetime=request.new_datetime,
            rescheduled_by_user_id=current_user["id"],
            reason=request.reason
        )
        
        return {
            "success": True,
            "message": "Interview rescheduled successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/interviews/{interview_id}/cancel")
async def cancel_interview(
    interview_id: str,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel an interview."""
    scheduler = InterviewScheduler(db)
    
    try:
        await scheduler.cancel_interview(
            interview_id=interview_id,
            cancelled_by_user_id=current_user["id"],
            reason=reason
        )
        
        return {
            "success": True,
            "message": "Interview cancelled successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/interviews/{interview_id}/complete")
async def complete_interview(
    interview_id: str,
    request: CompleteInterviewRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark interview as completed with feedback."""
    scheduler = InterviewScheduler(db)
    
    try:
        await scheduler.complete_interview(
            interview_id=interview_id,
            completed_by_user_id=current_user["id"],
            rating=request.rating,
            feedback=request.feedback,
            recommendation=request.recommendation,
            notes=request.notes
        )
        
        return {
            "success": True,
            "message": "Interview completed successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/interviews/statistics")
async def get_interview_statistics(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get interview statistics."""
    scheduler = InterviewScheduler(db)
    
    stats = await scheduler.get_interview_statistics()
    
    return {
        "success": True,
        "data": stats
    }
