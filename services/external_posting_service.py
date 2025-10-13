"""Service for posting jobs to external portals"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json

from models.database import Job, JobExternalPosting, generate_uuid

logger = logging.getLogger(__name__)


class ExternalPostingService:
    """Service for external job portal integrations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def post_to_portals(
        self,
        job_id: str,
        portals: List[str],
        field_mappings: Dict[str, Dict[str, Any]],
        expires_in_days: int,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Post job to multiple external portals
        
        Args:
            job_id: Job ID
            portals: List of portal names
            field_mappings: Portal-specific field mappings
            expires_in_days: Days until expiration
            user_id: User posting the job
        
        Returns:
            List of posting results for each portal
        
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
            
            postings = []
            
            for portal in portals:
                try:
                    # Create posting record
                    posting = await self._create_posting_record(
                        job_id=job_id,
                        portal=portal,
                        expires_in_days=expires_in_days
                    )
                    
                    # Post to portal (async - would be done in background)
                    # For now, just mark as pending
                    logger.info(f"Created external posting for job {job_id} on {portal}")
                    
                    postings.append({
                        "id": posting["id"],
                        "portal": portal,
                        "status": "pending",
                        "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
                    })
                
                except Exception as e:
                    logger.error(f"Error posting to {portal}: {str(e)}")
                    postings.append({
                        "portal": portal,
                        "status": "failed",
                        "error_message": str(e)
                    })
            
            return postings
        
        except Exception as e:
            logger.error(f"Error posting to portals: {str(e)}", exc_info=True)
            raise
    
    async def _create_posting_record(
        self,
        job_id: str,
        portal: str,
        expires_in_days: int
    ) -> Dict[str, Any]:
        """
        Create external posting record
        
        Args:
            job_id: Job ID
            portal: Portal name
            expires_in_days: Days until expiration
        
        Returns:
            Created posting details
        """
        try:
            # Check if posting already exists
            result = await self.db.execute(
                select(JobExternalPosting).where(
                    JobExternalPosting.job_id == job_id,
                    JobExternalPosting.portal == portal
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing
                existing.status = "pending"
                existing.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
                existing.updated_at = datetime.utcnow()
                await self.db.commit()
                return {"id": existing.id}
            else:
                # Create new
                posting = JobExternalPosting(
                    id=generate_uuid(),
                    job_id=job_id,
                    portal=portal,
                    status="pending",
                    expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
                )
                self.db.add(posting)
                await self.db.commit()
                return {"id": posting.id}
        
        except Exception as e:
            logger.error(f"Error creating posting record: {str(e)}")
            await self.db.rollback()
            raise
    
    async def _post_to_portal(
        self,
        job: Job,
        portal: str,
        field_mappings: Dict[str, Any],
        posting_id: str
    ) -> None:
        """
        Post job to specific portal
        This would be implemented with actual API calls
        
        Args:
            job: Job object
            portal: Portal name
            field_mappings: Portal-specific mappings
            posting_id: Posting record ID
        """
        try:
            if portal == "linkedin":
                await self._post_to_linkedin(job, field_mappings, posting_id)
            elif portal == "naukri":
                await self._post_to_naukri(job, field_mappings, posting_id)
            elif portal == "indeed":
                await self._post_to_indeed(job, field_mappings, posting_id)
        except Exception as e:
            # Update posting status to failed
            logger.error(f"Error posting to {portal}: {str(e)}")
            raise
    
    async def _post_to_linkedin(
        self,
        job: Job,
        field_mappings: Dict[str, Any],
        posting_id: str
    ) -> None:
        """Post job to LinkedIn - placeholder for actual implementation"""
        # Would use LinkedIn Jobs API with OAuth 2.0
        logger.info(f"LinkedIn posting placeholder for job {job.id}")
        pass
    
    async def _post_to_naukri(
        self,
        job: Job,
        field_mappings: Dict[str, Any],
        posting_id: str
    ) -> None:
        """Post job to Naukri - placeholder for actual implementation"""
        # Would use Naukri API
        logger.info(f"Naukri posting placeholder for job {job.id}")
        pass
    
    async def _post_to_indeed(
        self,
        job: Job,
        field_mappings: Dict[str, Any],
        posting_id: str
    ) -> None:
        """Post job to Indeed - placeholder for actual implementation"""
        # Would use Indeed API
        logger.info(f"Indeed posting placeholder for job {job.id}")
        pass
    
    async def get_job_postings(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Get all external postings for a job
        
        Args:
            job_id: Job ID
        
        Returns:
            List of external postings
        """
        try:
            result = await self.db.execute(
                select(JobExternalPosting).where(JobExternalPosting.job_id == job_id)
            )
            postings = result.scalars().all()
            
            return [
                {
                    "id": p.id,
                    "portal": p.portal,
                    "external_job_id": p.external_job_id,
                    "status": p.status,
                    "posted_at": p.posted_at,
                    "expires_at": p.expires_at,
                    "error_message": p.error_message
                }
                for p in postings
            ]
        
        except Exception as e:
            logger.error(f"Error fetching postings: {str(e)}")
            return []
    
    async def update_posting_status(
        self,
        posting_id: str,
        status: str,
        external_job_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update external posting status
        
        Args:
            posting_id: Posting ID
            status: New status
            external_job_id: External job ID from portal
            error_message: Error message if failed
        """
        try:
            result = await self.db.execute(
                select(JobExternalPosting).where(JobExternalPosting.id == posting_id)
            )
            posting = result.scalar_one_or_none()
            
            if posting:
                posting.status = status
                if external_job_id:
                    posting.external_job_id = external_job_id
                if error_message:
                    posting.error_message = error_message
                if status == "posted":
                    posting.posted_at = datetime.utcnow()
                posting.updated_at = datetime.utcnow()
                
                await self.db.commit()
                logger.info(f"Updated posting {posting_id} status to {status}")
        
        except Exception as e:
            logger.error(f"Error updating posting status: {str(e)}")
            await self.db.rollback()
