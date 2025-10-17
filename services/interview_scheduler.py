"""
Interview Scheduling Service - Phase 3 Day 5
=============================================
Manages interview scheduling, notifications, and conflict detection.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Interview, Candidate, Job, User
import uuid
import json

logger = logging.getLogger(__name__)


class InterviewScheduler:
    """Service for managing interview scheduling"""
    
    VALID_INTERVIEW_TYPES = {
        'phone', 'video', 'in_person', 'technical', 'hr_round', 'panel', 'behavioral'
    }
    
    VALID_STATUSES = {
        'scheduled', 'confirmed', 'completed', 'cancelled', 'no_show', 'rescheduled'
    }
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def schedule_interview(
        self,
        candidate_id: str,
        job_id: str,
        scheduled_by_user_id: str,
        scheduled_datetime: datetime,
        interview_type: str,
        duration_minutes: int = 60,
        interviewer_ids: Optional[List[str]] = None,
        location: Optional[str] = None,
        meeting_link: Optional[str] = None,
        notes: Optional[str] = None,
        interview_round: int = 1
    ) -> Interview:
        """
        Schedule a new interview.
        
        Args:
            candidate_id: Candidate ID
            job_id: Job ID
            scheduled_by_user_id: User scheduling the interview
            scheduled_datetime: Interview date and time
            interview_type: Type of interview
            duration_minutes: Duration in minutes
            interviewer_ids: List of interviewer user IDs
            location: Physical location or meeting details
            meeting_link: Video call link
            notes: Additional notes
            interview_round: Interview round number
        
        Returns:
            Interview object
        """
        # Validate interview type
        if interview_type not in self.VALID_INTERVIEW_TYPES:
            raise ValueError(f"Invalid interview type: {interview_type}")
        
        # Validate candidate exists
        candidate = await self.session.get(Candidate, candidate_id)
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")
        
        # Validate job exists
        job = await self.session.get(Job, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Check for conflicts
        conflicts = await self.check_conflicts(
            scheduled_datetime=scheduled_datetime,
            duration_minutes=duration_minutes,
            interviewer_ids=interviewer_ids or []
        )
        
        if conflicts:
            logger.warning(f"Interview conflicts detected: {len(conflicts)} conflicts")
        
        # Create interview
        interview = Interview(
            id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            job_id=job_id,
            scheduled_by=scheduled_by_user_id,
            interviewer_ids=json.dumps(interviewer_ids) if interviewer_ids else None,
            scheduled_datetime=scheduled_datetime,
            duration_minutes=duration_minutes,
            interview_type=interview_type,
            interview_round=interview_round,
            location=location,
            meeting_link=meeting_link,
            notes=notes,
            status='scheduled'
        )
        
        self.session.add(interview)
        await self.session.commit()
        await self.session.refresh(interview)
        
        logger.info(f"Scheduled {interview_type} interview for candidate {candidate_id}")
        
        return interview
    
    async def check_conflicts(
        self,
        scheduled_datetime: datetime,
        duration_minutes: int,
        interviewer_ids: List[str],
        exclude_interview_id: Optional[str] = None
    ) -> List[Interview]:
        """
        Check for scheduling conflicts.
        
        Args:
            scheduled_datetime: Proposed interview time
            duration_minutes: Duration in minutes
            interviewer_ids: List of interviewer IDs
            exclude_interview_id: Interview ID to exclude (for rescheduling)
        
        Returns:
            List of conflicting interviews
        """
        if not interviewer_ids:
            return []
        
        # Calculate time range
        end_datetime = scheduled_datetime + timedelta(minutes=duration_minutes)
        
        # Query for overlapping interviews
        query = select(Interview).where(
            and_(
                Interview.status.in_(['scheduled', 'confirmed']),
                Interview.scheduled_datetime < end_datetime,
                Interview.scheduled_datetime >= scheduled_datetime - timedelta(minutes=480)  # Check 8 hours before
            )
        )
        
        if exclude_interview_id:
            query = query.where(Interview.id != exclude_interview_id)
        
        result = await self.session.execute(query)
        interviews = result.scalars().all()
        
        # Filter by interviewer conflicts
        conflicts = []
        for interview in interviews:
            if interview.interviewer_ids:
                try:
                    interview_interviewers = json.loads(interview.interviewer_ids)
                    if any(iid in interviewer_ids for iid in interview_interviewers):
                        conflicts.append(interview)
                except:
                    pass
        
        return conflicts
    
    async def reschedule_interview(
        self,
        interview_id: str,
        new_datetime: datetime,
        rescheduled_by_user_id: str,
        reason: Optional[str] = None
    ) -> Interview:
        """
        Reschedule an existing interview.
        """
        interview = await self.session.get(Interview, interview_id)
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")
        
        if interview.status not in ['scheduled', 'confirmed']:
            raise ValueError(f"Cannot reschedule interview with status: {interview.status}")
        
        # Store original datetime
        if not interview.original_datetime:
            interview.original_datetime = interview.scheduled_datetime
        
        # Update interview
        interview.scheduled_datetime = new_datetime
        interview.rescheduled_by = rescheduled_by_user_id
        interview.reschedule_reason = reason
        interview.reschedule_count = (interview.reschedule_count or 0) + 1
        interview.status = 'rescheduled'
        
        await self.session.commit()
        await self.session.refresh(interview)
        
        logger.info(f"Rescheduled interview {interview_id} to {new_datetime}")
        
        return interview
    
    async def cancel_interview(
        self,
        interview_id: str,
        cancelled_by_user_id: str,
        reason: Optional[str] = None
    ) -> Interview:
        """Cancel an interview."""
        interview = await self.session.get(Interview, interview_id)
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")
        
        interview.status = 'cancelled'
        interview.cancelled_at = datetime.utcnow()
        interview.cancelled_by = cancelled_by_user_id
        interview.cancellation_reason = reason
        
        await self.session.commit()
        await self.session.refresh(interview)
        
        logger.info(f"Cancelled interview {interview_id}")
        
        return interview
    
    async def complete_interview(
        self,
        interview_id: str,
        completed_by_user_id: str,
        rating: Optional[int] = None,
        feedback: Optional[str] = None,
        recommendation: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Interview:
        """Mark interview as completed with feedback."""
        interview = await self.session.get(Interview, interview_id)
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")
        
        interview.status = 'completed'
        interview.completed_at = datetime.utcnow()
        interview.completed_by = completed_by_user_id
        interview.rating = rating
        interview.feedback = feedback
        interview.recommendation = recommendation
        if notes:
            interview.notes = notes
        
        await self.session.commit()
        await self.session.refresh(interview)
        
        logger.info(f"Completed interview {interview_id}")
        
        return interview
    
    async def get_candidate_interviews(
        self,
        candidate_id: str,
        include_cancelled: bool = False
    ) -> List[Interview]:
        """Get all interviews for a candidate."""
        query = select(Interview).where(Interview.candidate_id == candidate_id)
        
        if not include_cancelled:
            query = query.where(Interview.status != 'cancelled')
        
        query = query.order_by(Interview.scheduled_datetime.desc())
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_upcoming_interviews(
        self,
        days_ahead: int = 7,
        interviewer_id: Optional[str] = None
    ) -> List[Interview]:
        """Get upcoming interviews."""
        now = datetime.utcnow()
        future = now + timedelta(days=days_ahead)
        
        query = select(Interview).where(
            and_(
                Interview.scheduled_datetime >= now,
                Interview.scheduled_datetime <= future,
                Interview.status.in_(['scheduled', 'confirmed'])
            )
        ).order_by(Interview.scheduled_datetime)
        
        result = await self.session.execute(query)
        interviews = result.scalars().all()
        
        # Filter by interviewer if specified
        if interviewer_id:
            filtered = []
            for interview in interviews:
                if interview.interviewer_ids:
                    try:
                        interviewers = json.loads(interview.interviewer_ids)
                        if interviewer_id in interviewers:
                            filtered.append(interview)
                    except:
                        pass
            return filtered
        
        return interviews
    
    async def get_interview_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get interview statistics."""
        query = select(Interview)
        
        if start_date:
            query = query.where(Interview.scheduled_datetime >= start_date)
        if end_date:
            query = query.where(Interview.scheduled_datetime <= end_date)
        
        result = await self.session.execute(query)
        interviews = result.scalars().all()
        
        stats = {
            'total': len(interviews),
            'by_status': {},
            'by_type': {},
            'avg_rating': 0,
            'completion_rate': 0
        }
        
        # Count by status
        for interview in interviews:
            status = interview.status
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            itype = interview.interview_type
            stats['by_type'][itype] = stats['by_type'].get(itype, 0) + 1
        
        # Calculate averages
        completed = [i for i in interviews if i.status == 'completed']
        if completed:
            ratings = [i.rating for i in completed if i.rating]
            if ratings:
                stats['avg_rating'] = sum(ratings) / len(ratings)
            stats['completion_rate'] = (len(completed) / len(interviews)) * 100
        
        return stats
