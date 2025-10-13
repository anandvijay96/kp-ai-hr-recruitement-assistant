"""API endpoints for job management"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
import logging

from models.job_schemas import (
    JobCreateRequest, JobUpdateRequest, JobPublishRequest, JobCloseRequest,
    JobCloneRequest, AssignRecruitersRequest,
    PaginatedJobsResponse, StandardJobResponse, JobStatus
)
from services.job_service import JobService
from core.dependencies import get_current_user
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


def get_job_service(db: AsyncSession = Depends(get_db)) -> JobService:
    """Get job service instance"""
    return JobService(db_session=db)


# ============================================================================
# JOB CRUD ENDPOINTS
# ============================================================================

@router.post("", response_model=StandardJobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreateRequest,
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Create a new job requisition
    
    - **title**: Job title (required)
    - **department**: Department name
    - **location**: Location details
    - **work_type**: onsite, remote, or hybrid
    - **employment_type**: full_time, part_time, contract, internship
    - **description**: Job description (required)
    - **skills**: List of required skills
    - **status**: draft or open
    
    Returns created job details
    """
    try:
        logger.info(f"Creating job: {job_data.title} by user {current_user.get('email')}")
        
        # Check user permissions (managers and admins can create jobs)
        if current_user.get("role") not in ["admin", "manager"]:
            logger.warning(f"User {current_user.get('email')} with role {current_user.get('role')} attempted to create job")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only managers and admins can create jobs"
            )
        
        job = await job_service.create_job(
            job_data=job_data,
            created_by=current_user["id"]
        )
        
        logger.info(f"Job created successfully: {job['id']}")
        
        return StandardJobResponse(
            success=True,
            message="Job created successfully",
            data=job
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error creating job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@router.get("", response_model=PaginatedJobsResponse)
async def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by title, department"),
    status: Optional[JobStatus] = Query(None, description="Filter by status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    work_type: Optional[str] = Query(None, description="Filter by work type"),
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Get paginated list of jobs
    
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    - **search**: Search term for title, department
    - **status**: Filter by job status
    - **department**: Filter by department
    - **work_type**: Filter by work type
    
    Returns paginated list of jobs
    """
    try:
        result = await job_service.search_jobs(
            search=search,
            status=status.value if status else None,
            department=department,
            work_type=work_type,
            page=page,
            limit=limit,
            user_id=current_user["id"],
            user_role=current_user["role"]
        )
        
        return PaginatedJobsResponse(
            success=True,
            data=result
        )
    
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs"
        )


@router.get("/{job_id}", response_model=StandardJobResponse)
async def get_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Get detailed information about a job
    
    - **job_id**: Job UUID
    
    Returns complete job details including skills, recruiters, and documents
    """
    try:
        job = await job_service.get_job_by_id(
            job_id=job_id,
            include_relations=True
        )
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        return StandardJobResponse(
            success=True,
            data=job
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job details"
        )


@router.patch("/{job_id}", response_model=StandardJobResponse)
async def update_job(
    job_id: str,
    update_data: JobUpdateRequest,
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Update job information (partial updates allowed)
    
    - **job_id**: Job UUID
    - **update_data**: Fields to update
    
    Only the creator, assigned managers, or admins can update
    """
    try:
        logger.info(f"Updating job {job_id} by user {current_user.get('email')}")
        logger.info(f"Update data: {update_data.model_dump(exclude_unset=True)}")
        
        # Check permissions
        job = await job_service.get_job_by_id(job_id, include_relations=False)
        if not job:
            logger.warning(f"Job {job_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Permission check
        if current_user["role"] not in ["admin"] and job["created_by"]["id"] != current_user["id"]:
            logger.warning(f"User {current_user.get('email')} doesn't have permission to update job {job_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this job"
            )
        
        updated_job = await job_service.update_job(
            job_id=job_id,
            update_data=update_data
        )
        
        logger.info(f"Job {job_id} updated successfully")
        
        return StandardJobResponse(
            success=True,
            message="Job updated successfully",
            data=updated_job
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update job: {str(e)}"
        )


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Delete a job (only drafts can be deleted)
    
    - **job_id**: Job UUID
    
    Only admins or the creator can delete draft jobs
    """
    try:
        # Check permissions
        if current_user["role"] != "admin":
            job = await job_service.get_job_by_id(job_id, include_relations=False)
            if not job or job["created_by"]["id"] != current_user["id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this job"
                )
            if job["status"] != "draft":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only draft jobs can be deleted"
                )
        
        success = await job_service.delete_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        return {
            "success": True,
            "message": "Job deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job"
        )


# ============================================================================
# JOB WORKFLOW ENDPOINTS
# ============================================================================

@router.post("/{job_id}/publish", response_model=StandardJobResponse)
async def publish_job(
    job_id: str,
    publish_data: JobPublishRequest,
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Publish a draft job (change status from draft to open)
    
    - **job_id**: Job UUID
    - **send_notifications**: Send email notifications to recruiters
    
    Returns updated job with published status
    """
    try:
        job = await job_service.publish_job(
            job_id=job_id,
            published_by=current_user["id"],
            send_notifications=publish_data.send_notifications
        )
        
        return StandardJobResponse(
            success=True,
            message="Job published successfully",
            data=job
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error publishing job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish job"
        )


@router.post("/{job_id}/close", response_model=StandardJobResponse)
async def close_job(
    job_id: str,
    close_data: JobCloseRequest,
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Close a job (mark as filled, cancelled, etc.)
    
    - **job_id**: Job UUID
    - **close_reason**: Reason for closing (filled, cancelled, budget_cut, position_eliminated)
    - **notes**: Additional notes
    
    Returns updated job with closed status
    """
    try:
        job = await job_service.close_job(
            job_id=job_id,
            close_reason=close_data.close_reason.value,
            notes=close_data.notes,
            closed_by=current_user["id"]
        )
        
        return StandardJobResponse(
            success=True,
            message="Job closed successfully",
            data=job
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error closing job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close job"
        )


@router.post("/{job_id}/reopen", response_model=StandardJobResponse)
async def reopen_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Reopen a closed or on-hold job
    
    - **job_id**: Job UUID
    
    Returns updated job with open status
    """
    try:
        job = await job_service.reopen_job(
            job_id=job_id,
            reopened_by=current_user["id"]
        )
        
        return StandardJobResponse(
            success=True,
            message="Job reopened successfully",
            data=job
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error reopening job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reopen job"
        )


# ============================================================================
# JOB CLONING
# ============================================================================

@router.post("/{job_id}/clone", response_model=StandardJobResponse, status_code=status.HTTP_201_CREATED)
async def clone_job(
    job_id: str,
    clone_data: JobCloneRequest,
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Clone an existing job
    
    - **job_id**: Job UUID to clone
    - **new_title**: Optional new title for cloned job
    - **modify_fields**: Optional fields to modify in cloned job
    
    Returns newly created job
    """
    try:
        if current_user.get("role") not in ["admin", "manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only managers and admins can clone jobs"
            )
        
        cloned_job = await job_service.clone_job(
            job_id=job_id,
            new_title=clone_data.new_title,
            modify_fields=clone_data.modify_fields,
            created_by=current_user["id"]
        )
        
        return StandardJobResponse(
            success=True,
            message="Job cloned successfully",
            data=cloned_job
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error cloning job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clone job"
        )


# ============================================================================
# RECRUITER ASSIGNMENT
# ============================================================================

@router.post("/{job_id}/recruiters", response_model=StandardJobResponse)
async def assign_recruiters(
    job_id: str,
    assignment_data: AssignRecruitersRequest,
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Assign recruiters to a job
    
    - **job_id**: Job UUID
    - **recruiters**: List of recruiter assignments with primary flag
    - **send_notifications**: Send email notifications to recruiters
    
    Returns updated job with assigned recruiters
    """
    try:
        job = await job_service.assign_recruiters(
            job_id=job_id,
            recruiters=assignment_data.recruiters,
            assigned_by=current_user["id"],
            send_notifications=assignment_data.send_notifications
        )
        
        return StandardJobResponse(
            success=True,
            message="Recruiters assigned successfully",
            data=job
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error assigning recruiters to job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign recruiters"
        )


@router.delete("/{job_id}/recruiters/{user_id}")
async def remove_recruiter(
    job_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Remove a recruiter from a job
    
    - **job_id**: Job UUID
    - **user_id**: User UUID to remove
    
    Returns success message
    """
    try:
        await job_service.remove_recruiter(
            job_id=job_id,
            user_id=user_id,
            removed_by=current_user["id"]
        )
        
        return {
            "success": True,
            "message": "Recruiter removed successfully"
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error removing recruiter from job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove recruiter"
        )


# ============================================================================
# STATISTICS & ANALYTICS
# ============================================================================

@router.get("/stats/overview")
async def get_job_statistics(
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """
    Get job statistics overview
    
    Returns counts by status, department, and other metrics
    """
    try:
        stats = await job_service.get_statistics(
            user_id=current_user["id"],
            user_role=current_user["role"]
        )
        
        return {
            "success": True,
            "data": stats
        }
    
    except Exception as e:
        logger.error(f"Error getting job statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )
