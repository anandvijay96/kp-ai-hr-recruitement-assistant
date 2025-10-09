"""Service layer for Jobs Management business logic"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from fastapi import HTTPException
import logging

from models.database import Job, User, JobStatusHistory, JobExternalPosting
from models.job_management_schemas import (
    JobStatus, DashboardResponse, JobSummaryResponse,
    PaginationInfo, DashboardSummary
)

logger = logging.getLogger(__name__)


class JobManagementService:
    """Service for jobs management operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_dashboard(
        self,
        status: Optional[JobStatus] = None,
        department: Optional[str] = None,
        hiring_manager_id: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 20
    ) -> DashboardResponse:
        """
        Get dashboard with filters, search, and pagination
        
        Args:
            status: Filter by job status
            department: Filter by department
            hiring_manager_id: Filter by hiring manager
            date_from: Filter from date
            date_to: Filter to date
            search: Search query
            sort_by: Sort field
            sort_order: Sort order (asc/desc)
            page: Page number
            limit: Items per page
        
        Returns:
            Dashboard response with jobs, pagination, and summary
        """
        try:
            # Build base query
            query = select(Job).where(Job.deleted_at.is_(None))
            
            # Apply filters
            if status:
                query = query.where(Job.status == status.value)
            if department:
                query = query.where(Job.department == department)
            if hiring_manager_id:
                query = query.where(Job.created_by == hiring_manager_id)
            if date_from:
                query = query.where(Job.created_at >= datetime.combine(date_from, datetime.min.time()))
            if date_to:
                query = query.where(Job.created_at <= datetime.combine(date_to, datetime.max.time()))
            if search:
                search_term = f"%{search}%"
                query = query.where(
                    or_(
                        Job.title.ilike(search_term),
                        Job.description.ilike(search_term),
                        Job.uuid.ilike(search_term)
                    )
                )
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0
            
            # Apply sorting
            sort_column = getattr(Job, sort_by, Job.created_at)
            if sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # Apply pagination
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            jobs = result.scalars().all()
            
            # Get summary counts
            summary = await self._get_summary_counts()
            
            # Format jobs
            job_summaries = []
            for job in jobs:
                job_summary = await self._format_job_summary(job)
                job_summaries.append(job_summary)
            
            # Calculate pagination
            total_pages = (total + limit - 1) // limit
            
            return DashboardResponse(
                jobs=job_summaries,
                pagination=PaginationInfo(
                    total=total,
                    page=page,
                    limit=limit,
                    total_pages=total_pages
                ),
                summary=summary
            )
        
        except Exception as e:
            logger.error(f"Error fetching dashboard: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard: {str(e)}")
    
    async def update_status(
        self,
        job_id: str,
        new_status: JobStatus,
        reason: Optional[str],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Update job status with validation and audit logging
        
        Args:
            job_id: Job ID
            new_status: New status
            reason: Reason for change
            user_id: User making the change
        
        Returns:
            Updated job information
        """
        try:
            # Get job
            query = select(Job).where(Job.id == job_id)
            result = await self.db.execute(query)
            job = result.scalar_one_or_none()
            
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            old_status = job.status
            
            # Validate status transition
            if not self._is_valid_transition(old_status, new_status.value):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status transition from {old_status} to {new_status.value}"
                )
            
            # Update status
            job.status = new_status.value
            
            # Update timestamps
            if new_status == JobStatus.CLOSED:
                job.closed_at = datetime.utcnow()
            elif new_status == JobStatus.ARCHIVED:
                job.archived_at = datetime.utcnow()
            
            # Create status history record
            history = JobStatusHistory(
                job_id=job_id,
                old_status=old_status,
                new_status=new_status.value,
                reason=reason,
                changed_by=user_id
            )
            self.db.add(history)
            
            await self.db.commit()
            await self.db.refresh(job)
            
            logger.info(f"Job {job_id} status updated from {old_status} to {new_status.value} by user {user_id}")
            
            return {
                "id": job_id,
                "status": job.status,
                "closed_at": job.closed_at.isoformat() if job.closed_at else None,
                "archived_at": job.archived_at.isoformat() if job.archived_at else None,
                "message": "Job status updated successfully"
            }
        
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating job status: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to update job status: {str(e)}")
    
    async def delete_job(
        self,
        job_id: str,
        permanent: bool,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Soft delete (archive) or permanently delete a job
        
        Args:
            job_id: Job ID
            permanent: Whether to permanently delete
            user_id: User performing deletion
        
        Returns:
            Deletion confirmation
        """
        try:
            query = select(Job).where(Job.id == job_id)
            result = await self.db.execute(query)
            job = result.scalar_one_or_none()
            
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            if permanent:
                # Permanent delete (requires super admin)
                await self.db.delete(job)
                message = "Job permanently deleted"
                status_value = "deleted"
            else:
                # Soft delete (archive)
                job.status = "archived"
                job.archived_at = datetime.utcnow()
                message = "Job archived successfully"
                status_value = "archived"
            
            await self.db.commit()
            
            logger.info(f"Job {job_id} {'permanently deleted' if permanent else 'archived'} by user {user_id}")
            
            return {
                "id": job_id,
                "status": status_value,
                "archived_at": job.archived_at.isoformat() if not permanent and job.archived_at else None,
                "message": message
            }
        
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting job: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")
    
    def _is_valid_transition(self, old_status: str, new_status: str) -> bool:
        """
        Validate status transitions
        
        Args:
            old_status: Current status
            new_status: Desired new status
        
        Returns:
            True if transition is valid
        """
        valid_transitions = {
            "draft": ["open", "closed", "archived"],
            "open": ["closed", "on_hold", "archived"],
            "on_hold": ["open", "closed", "archived"],
            "closed": ["archived"],
            "archived": []  # Cannot transition from archived
        }
        return new_status in valid_transitions.get(old_status, [])
    
    async def _format_job_summary(self, job: Job) -> JobSummaryResponse:
        """
        Format job for dashboard display
        
        Args:
            job: Job model instance
        
        Returns:
            Formatted job summary
        """
        try:
            # Get hiring manager info
            hiring_manager_query = select(User).where(User.id == job.created_by)
            hm_result = await self.db.execute(hiring_manager_query)
            hiring_manager = hm_result.scalar_one_or_none()
            
            # Get external postings
            postings_query = select(JobExternalPosting.portal).where(
                and_(
                    JobExternalPosting.job_id == job.id,
                    JobExternalPosting.status == "posted"
                )
            )
            postings_result = await self.db.execute(postings_query)
            external_postings = [row[0] for row in postings_result.all()]
            
            return JobSummaryResponse(
                id=job.id,
                uuid=job.uuid,
                title=job.title,
                department=job.department,
                status=job.status,
                posted_date=job.published_at,
                application_deadline=job.closing_date,
                application_count=0,  # TODO: Get from applications table
                avg_match_score=None,  # TODO: Calculate from applications
                hiring_manager={
                    "id": job.created_by,
                    "name": hiring_manager.full_name if hiring_manager else "Unknown",
                    "email": hiring_manager.email if hiring_manager else ""
                },
                external_postings=external_postings,
                last_updated=job.updated_at,
                view_count=job.view_count or 0
            )
        
        except Exception as e:
            logger.error(f"Error formatting job summary: {str(e)}")
            # Return basic info if formatting fails
            return JobSummaryResponse(
                id=job.id,
                uuid=job.uuid,
                title=job.title,
                department=job.department,
                status=job.status,
                posted_date=job.published_at,
                application_deadline=job.closing_date,
                application_count=0,
                avg_match_score=None,
                hiring_manager={"id": job.created_by, "name": "Unknown", "email": ""},
                external_postings=[],
                last_updated=job.updated_at,
                view_count=job.view_count or 0
            )
    
    async def _get_summary_counts(self) -> DashboardSummary:
        """
        Get summary counts for dashboard
        
        Returns:
            Dashboard summary with counts
        """
        try:
            # Count total jobs
            total_query = select(func.count()).select_from(Job)
            total_result = await self.db.execute(total_query)
            total = total_result.scalar() or 0
            
            # Count by status
            open_query = select(func.count()).select_from(Job).where(Job.status == "open")
            open_result = await self.db.execute(open_query)
            open_count = open_result.scalar() or 0
            
            closed_query = select(func.count()).select_from(Job).where(Job.status == "closed")
            closed_result = await self.db.execute(closed_query)
            closed_count = closed_result.scalar() or 0
            
            on_hold_query = select(func.count()).select_from(Job).where(Job.status == "on_hold")
            on_hold_result = await self.db.execute(on_hold_query)
            on_hold_count = on_hold_result.scalar() or 0
            
            archived_query = select(func.count()).select_from(Job).where(Job.status == "archived")
            archived_result = await self.db.execute(archived_query)
            archived_count = archived_result.scalar() or 0
            
            return DashboardSummary(
                total_jobs=total,
                open=open_count,
                closed=closed_count,
                on_hold=on_hold_count,
                archived=archived_count
            )
        
        except Exception as e:
            logger.error(f"Error getting summary counts: {str(e)}")
            return DashboardSummary(
                total_jobs=0,
                open=0,
                closed=0,
                on_hold=0,
                archived=0
            )
