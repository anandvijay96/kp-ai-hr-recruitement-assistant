"""Job Applications API - Apply candidates to jobs"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid
import logging
from datetime import datetime

from core.database import get_db
from core.auth import require_auth
from models.database import JobApplication, Job, Candidate
from fastapi import Request

router = APIRouter()
logger = logging.getLogger(__name__)


class JobApplicationCreate(BaseModel):
    """Request model for creating job application"""
    candidate_id: str
    status: str = "applied"


class JobApplicationResponse(BaseModel):
    """Response model for job application"""
    id: str
    job_id: str
    candidate_id: str
    status: str
    applied_at: datetime


@router.post("/{job_id}/applications", response_model=JobApplicationResponse)
async def create_job_application(
    job_id: str,
    application_data: JobApplicationCreate,
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """
    Apply a candidate to a job
    
    Args:
        job_id: Job UUID
        application_data: Application data (candidate_id, status)
        
    Returns:
        Created job application
    """
    try:
        # Verify job exists
        job_result = await db.execute(
            select(Job).where(Job.id == job_id)
        )
        job = job_result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Verify candidate exists
        candidate_result = await db.execute(
            select(Candidate).where(Candidate.id == application_data.candidate_id)
        )
        candidate = candidate_result.scalar_one_or_none()
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        # Check if application already exists
        existing_result = await db.execute(
            select(JobApplication).where(
                JobApplication.job_id == job_id,
                JobApplication.candidate_id == application_data.candidate_id
            )
        )
        existing_app = existing_result.scalar_one_or_none()
        
        if existing_app:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Candidate has already applied to this job"
            )
        
        # Create job application
        job_application = JobApplication(
            id=str(uuid.uuid4()),
            job_id=job_id,
            candidate_id=application_data.candidate_id,
            status=application_data.status,
            applied_at=datetime.utcnow()
        )
        
        db.add(job_application)
        await db.commit()
        await db.refresh(job_application)
        
        logger.info(f"Created job application for candidate {application_data.candidate_id} to job {job_id}")
        
        return JobApplicationResponse(
            id=job_application.id,
            job_id=job_application.job_id,
            candidate_id=job_application.candidate_id,
            status=job_application.status,
            applied_at=job_application.applied_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job application: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job application"
        )
