"""Service for bulk operations on jobs"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from datetime import datetime
import logging
import json

from models.database import Job, BulkOperation, generate_uuid

logger = logging.getLogger(__name__)


class BulkOperationsService:
    """Service for bulk job operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_bulk_operation(
        self,
        job_ids: List[str],
        operation_type: str,
        parameters: Dict[str, Any],
        initiated_by: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Create a bulk operation record
        
        Args:
            job_ids: List of job IDs
            operation_type: Type of operation
            parameters: Operation parameters
            initiated_by: User ID
            dry_run: If True, don't actually execute
        
        Returns:
            Bulk operation details
        
        Raises:
            ValueError: If validation fails
        """
        try:
            # Validate job count
            if len(job_ids) > 50:
                raise ValueError("Maximum 50 jobs allowed per bulk operation")
            
            # Verify all jobs exist
            result = await self.db.execute(
                select(Job).where(Job.id.in_(job_ids))
            )
            jobs = result.scalars().all()
            
            if len(jobs) != len(job_ids):
                raise ValueError("One or more jobs not found")
            
            # Create bulk operation record
            operation_id = generate_uuid()
            operation = BulkOperation(
                id=operation_id,
                operation_type=operation_type,
                job_ids=json.dumps(job_ids),
                parameters=json.dumps(parameters),
                status="dry_run" if dry_run else "pending",
                total_count=len(job_ids),
                initiated_by=initiated_by
            )
            
            self.db.add(operation)
            await self.db.commit()
            
            logger.info(f"Created bulk operation {operation_id} for {len(job_ids)} jobs")
            
            return {
                "success": True,
                "operation_id": operation_id,
                "status": operation.status,
                "total_count": operation.total_count,
                "success_count": 0,
                "failure_count": 0,
                "error_details": [],
                "started_at": None,
                "completed_at": None
            }
        
        except Exception as e:
            logger.error(f"Error creating bulk operation: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def process_bulk_operation(self, operation_id: str) -> None:
        """
        Process a bulk operation
        This would typically be called as a background task
        
        Args:
            operation_id: Operation ID
        """
        try:
            # Get operation
            result = await self.db.execute(
                select(BulkOperation).where(BulkOperation.id == operation_id)
            )
            operation = result.scalar_one_or_none()
            
            if not operation:
                raise ValueError("Operation not found")
            
            # Update status
            operation.status = "processing"
            operation.started_at = datetime.utcnow()
            await self.db.commit()
            
            # Parse job IDs and parameters
            job_ids = json.loads(operation.job_ids)
            parameters = json.loads(operation.parameters)
            
            success_count = 0
            failure_count = 0
            errors = []
            
            # Process each job
            for job_id in job_ids:
                try:
                    await self._process_single_job(
                        job_id,
                        operation.operation_type,
                        parameters
                    )
                    success_count += 1
                except Exception as e:
                    failure_count += 1
                    errors.append({
                        "job_id": job_id,
                        "error": str(e)
                    })
                    logger.error(f"Error processing job {job_id}: {str(e)}")
            
            # Update operation status
            operation.success_count = success_count
            operation.failure_count = failure_count
            operation.error_details = json.dumps(errors) if errors else None
            operation.status = "completed" if failure_count == 0 else "partial"
            operation.completed_at = datetime.utcnow()
            
            await self.db.commit()
            logger.info(f"Bulk operation {operation_id} completed: {success_count} success, {failure_count} failed")
        
        except Exception as e:
            logger.error(f"Error processing bulk operation: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def _process_single_job(
        self,
        job_id: str,
        operation_type: str,
        parameters: Dict[str, Any]
    ) -> None:
        """Process a single job in bulk operation"""
        result = await self.db.execute(
            select(Job).where(Job.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        if operation_type == "status_update":
            job.status = parameters.get("status")
            job.updated_at = datetime.utcnow()
        elif operation_type == "archive":
            job.status = "archived"
            job.archived_at = datetime.utcnow()
        elif operation_type == "update_deadline":
            job.application_deadline = parameters.get("deadline")
        
        await self.db.commit()
    
    async def get_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """
        Get status of a bulk operation
        
        Args:
            operation_id: Operation ID
        
        Returns:
            Operation status details
        """
        try:
            result = await self.db.execute(
                select(BulkOperation).where(BulkOperation.id == operation_id)
            )
            operation = result.scalar_one_or_none()
            
            if not operation:
                raise ValueError("Operation not found")
            
            return {
                "operation_id": operation.id,
                "operation_type": operation.operation_type,
                "status": operation.status,
                "total_count": operation.total_count,
                "success_count": operation.success_count,
                "failure_count": operation.failure_count,
                "error_details": json.loads(operation.error_details) if operation.error_details else [],
                "started_at": operation.started_at,
                "completed_at": operation.completed_at
            }
        
        except Exception as e:
            logger.error(f"Error fetching operation status: {str(e)}", exc_info=True)
            raise
