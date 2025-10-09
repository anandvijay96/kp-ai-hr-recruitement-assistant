"""Service for Jobs Management operations"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update as sql_update
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
import json

from models.database import (
    Job, User, JobRecruiter, JobStatusHistory, JobExternalPosting,
    generate_uuid
)
from models.jobs_management_schemas import JobManagementStatus

logger = logging.getLogger(__name__)


class JobsManagementService:
    """Service for jobs management operations"""
    
    # Valid status transitions
    VALID_TRANSITIONS = {
        "draft": ["open"],
        "open": ["on_hold", "closed"],
        "on_hold": ["open", "closed"],
        "closed": ["archived"],
        "archived": []  # Cannot transition from archived
    }
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_dashboard(
        self,
        user_id: str,
        user_role: str,
        status: Optional[str] = None,
        department: Optional[str] = None,
        hiring_manager_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get jobs dashboard with filters and pagination
        
        Args:
            user_id: Current user ID
            user_role: Current user role
            status: Filter by status
            department: Filter by department
            hiring_manager_id: Filter by hiring manager
            date_from: Start date filter
            date_to: End date filter
            search: Search term
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            page: Page number
            limit: Items per page
        
        Returns:
            Dictionary with jobs list, pagination, and summary
        """
        try:
            # Build base query
            query = select(Job)
            
            # Apply filters
            if status:
                query = query.where(Job.status == status)
            
            if department:
                query = query.where(Job.department == department)
            
            if hiring_manager_id:
                query = query.where(Job.created_by == hiring_manager_id)
            
            if date_from:
                query = query.where(Job.created_at >= datetime.fromisoformat(date_from))
            
            if date_to:
                query = query.where(Job.created_at <= datetime.fromisoformat(date_to))
            
            if search:
                search_term = f"%{search}%"
                query = query.where(
                    or_(
                        Job.title.ilike(search_term),
                        Job.department.ilike(search_term),
                        Job.search_text.ilike(search_term)
                    )
                )
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            result = await self.db.execute(count_query)
            total = result.scalar() or 0
            
            # Apply sorting
            sort_column = getattr(Job, sort_by, Job.created_at)
            if sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
            
            # Apply pagination
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            jobs = result.scalars().all()
            
            # Format jobs for response
            jobs_list = []
            for job in jobs:
                # Get hiring manager info
                hiring_manager = None
                if job.created_by:
                    hm_result = await self.db.execute(
                        select(User).where(User.id == job.created_by)
                    )
                    hm = hm_result.scalar_one_or_none()
                    if hm:
                        hiring_manager = {
                            "id": hm.id,
                            "name": hm.full_name,
                            "email": hm.email
                        }
                
                # Get external postings
                ext_result = await self.db.execute(
                    select(JobExternalPosting).where(JobExternalPosting.job_id == job.id)
                )
                external_postings = [p.portal for p in ext_result.scalars().all()]
                
                jobs_list.append({
                    "id": job.id,
                    "uuid": job.uuid,
                    "title": job.title,
                    "department": job.department,
                    "status": job.status,
                    "posted_date": job.published_at,
                    "application_deadline": job.application_deadline,
                    "application_count": 0,  # TODO: Get from applications table
                    "avg_match_score": None,  # TODO: Get from analytics
                    "hiring_manager": hiring_manager,
                    "external_postings": external_postings,
                    "last_updated": job.updated_at,
                    "view_count": job.view_count or 0
                })
            
            # Get summary statistics
            summary_query = select(
                Job.status,
                func.count(Job.id).label('count')
            ).group_by(Job.status)
            
            summary_result = await self.db.execute(summary_query)
            summary_rows = summary_result.all()
            
            summary = {
                "total_jobs": total,
                "open": 0,
                "closed": 0,
                "on_hold": 0,
                "archived": 0,
                "draft": 0
            }
            
            for row in summary_rows:
                status_key = row.status
                if status_key in summary:
                    summary[status_key] = row.count
            
            return {
                "success": True,
                "jobs": jobs_list,
                "pagination": {
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "total_pages": (total + limit - 1) // limit if total > 0 else 0
                },
                "summary": summary
            }
        
        except Exception as e:
            logger.error(f"Error fetching dashboard: {str(e)}", exc_info=True)
            raise
    
    async def update_job_status(
        self,
        job_id: str,
        new_status: str,
        reason: Optional[str],
        user_id: str,
        user_role: str
    ) -> Dict[str, Any]:
        """
        Update job status with validation
        
        Args:
            job_id: Job ID
            new_status: New status
            reason: Reason for status change
            user_id: User making the change
            user_role: User's role
        
        Returns:
            Updated job details with old_status for audit
        
        Raises:
            ValueError: If job not found or invalid transition
        """
        try:
            # Get job
            result = await self.db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                raise ValueError("Job not found")
            
            # Store old status
            old_status = job.status
            
            # Validate status transition
            if new_status not in self.VALID_TRANSITIONS.get(old_status, []):
                raise ValueError(
                    f"Invalid status transition from '{old_status}' to '{new_status}'. "
                    f"Valid transitions: {self.VALID_TRANSITIONS.get(old_status, [])}"
                )
            
            # Check permissions for certain transitions
            if new_status == "archived" and user_role not in ["admin"]:
                raise ValueError("Only admins can archive jobs")
            
            # Require reason for closing
            if new_status == "closed" and not reason:
                raise ValueError("Reason is required when closing a job")
            
            # Update status
            job.status = new_status
            
            # Set timestamps
            if new_status == "closed":
                job.closed_at = datetime.utcnow()
                if reason:
                    job.close_reason = reason
            elif new_status == "archived":
                job.archived_at = datetime.utcnow()
            elif new_status == "open" and old_status == "draft":
                job.published_at = datetime.utcnow()
            
            job.updated_at = datetime.utcnow()
            
            # Create status history entry
            history = JobStatusHistory(
                id=generate_uuid(),
                job_id=job_id,
                from_status=old_status,
                to_status=new_status,
                reason=reason,
                changed_by=user_id
            )
            self.db.add(history)
            
            await self.db.commit()
            await self.db.refresh(job)
            
            logger.info(f"Job {job_id} status updated from {old_status} to {new_status} by user {user_id}")
            
            return {
                "success": True,
                "id": job.id,
                "status": job.status,
                "old_status": old_status,
                "closed_at": job.closed_at,
                "archived_at": job.archived_at,
                "message": f"Job status updated to {new_status}"
            }
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating job status: {str(e)}", exc_info=True)
            raise
    
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
            permanent: If True, permanently delete
            user_id: User performing deletion
        
        Returns:
            Deletion result
        
        Raises:
            ValueError: If job not found
        """
        try:
            # Get job
            result = await self.db.execute(
                select(Job).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                raise ValueError("Job not found")
            
            if permanent:
                # Permanent delete
                await self.db.delete(job)
                logger.info(f"Job {job_id} permanently deleted by user {user_id}")
                message = "Job permanently deleted"
            else:
                # Soft delete (archive)
                job.status = "archived"
                job.archived_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                logger.info(f"Job {job_id} archived by user {user_id}")
                message = "Job archived successfully. Can be restored within 90 days."
            
            await self.db.commit()
            
            return {
                "success": True,
                "id": job_id,
                "deleted": permanent,
                "archived_at": job.archived_at if not permanent else None,
                "message": message
            }
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting job: {str(e)}", exc_info=True)
            raise
    
    async def increment_view_count(self, job_id: str) -> None:
        """
        Increment job view count
        
        Args:
            job_id: Job ID
        """
        try:
            await self.db.execute(
                sql_update(Job)
                .where(Job.id == job_id)
                .values(view_count=Job.view_count + 1)
            )
            await self.db.commit()
            logger.debug(f"Incremented view count for job {job_id}")
        except Exception as e:
            logger.error(f"Error incrementing view count: {str(e)}")
            await self.db.rollback()
    
    async def get_job_status_history(
        self,
        job_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get status change history for a job
        
        Args:
            job_id: Job ID
            limit: Maximum number of entries to return
        
        Returns:
            List of status history entries
        """
        try:
            result = await self.db.execute(
                select(JobStatusHistory)
                .where(JobStatusHistory.job_id == job_id)
                .order_by(JobStatusHistory.changed_at.desc())
                .limit(limit)
            )
            history = result.scalars().all()
            
            history_list = []
            for entry in history:
                # Get user info
                user_result = await self.db.execute(
                    select(User).where(User.id == entry.changed_by)
                )
                user = user_result.scalar_one_or_none()
                
                history_list.append({
                    "id": entry.id,
                    "from_status": entry.from_status,
                    "to_status": entry.to_status,
                    "reason": entry.reason,
                    "changed_by": {
                        "id": user.id,
                        "name": user.full_name
                    } if user else None,
                    "changed_at": entry.changed_at
                })
            
            return history_list
        
        except Exception as e:
            logger.error(f"Error fetching status history: {str(e)}", exc_info=True)
            raise
