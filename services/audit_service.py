"""Service for audit logging"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import json
import hashlib

from models.database import JobAuditLog, User, generate_uuid

logger = logging.getLogger(__name__)


class AuditService:
    """Service for creating and querying audit logs"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def log_status_change(
        self,
        job_id: str,
        old_status: Optional[str],
        new_status: str,
        reason: Optional[str],
        user_id: str,
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> None:
        """
        Log job status change
        
        Args:
            job_id: Job ID
            old_status: Previous status
            new_status: New status
            reason: Reason for change
            user_id: User making the change
            ip_address: IP address
            user_agent: User agent string
        """
        try:
            await self._create_audit_entry(
                job_id=job_id,
                action_type="status_change",
                entity_type="job_status",
                old_values={"status": old_status, "reason": reason},
                new_values={"status": new_status},
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception as e:
            logger.error(f"Error logging status change: {str(e)}", exc_info=True)
    
    async def log_deletion(
        self,
        job_id: str,
        permanent: bool,
        user_id: str,
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> None:
        """
        Log job deletion
        
        Args:
            job_id: Job ID
            permanent: Whether deletion is permanent
            user_id: User performing deletion
            ip_address: IP address
            user_agent: User agent string
        """
        try:
            await self._create_audit_entry(
                job_id=job_id,
                action_type="delete",
                entity_type="job",
                old_values={},
                new_values={"permanent": permanent},
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception as e:
            logger.error(f"Error logging deletion: {str(e)}", exc_info=True)
    
    async def log_bulk_operation(
        self,
        job_id: str,
        operation_type: str,
        parameters: Dict[str, Any],
        user_id: str,
        ip_address: Optional[str]
    ) -> None:
        """Log bulk operation on a job"""
        try:
            await self._create_audit_entry(
                job_id=job_id,
                action_type="bulk_update",
                entity_type="job",
                old_values={},
                new_values={"operation": operation_type, "parameters": parameters},
                user_id=user_id,
                ip_address=ip_address,
                user_agent=None
            )
        except Exception as e:
            logger.error(f"Error logging bulk operation: {str(e)}")
    
    async def _create_audit_entry(
        self,
        job_id: str,
        action_type: str,
        entity_type: str,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        user_id: str,
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> None:
        """
        Create audit log entry with checksum
        
        Args:
            job_id: Job ID
            action_type: Type of action
            entity_type: Type of entity
            old_values: Previous values
            new_values: New values
            user_id: User ID
            ip_address: IP address
            user_agent: User agent
        """
        try:
            timestamp = datetime.utcnow()
            
            # Generate checksum for tamper detection
            checksum_data = f"{job_id}{action_type}{user_id}{timestamp.isoformat()}"
            checksum = hashlib.sha256(checksum_data.encode()).hexdigest()
            
            # Create audit log entry
            audit_log = JobAuditLog(
                id=generate_uuid(),
                job_id=job_id,
                action_type=action_type,
                entity_type=entity_type,
                old_values=json.dumps(old_values),
                new_values=json.dumps(new_values),
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=timestamp,
                checksum=checksum
            )
            
            self.db.add(audit_log)
            await self.db.commit()
            
            logger.info(f"Created audit log entry for job {job_id}, action: {action_type}")
        
        except Exception as e:
            logger.error(f"Error creating audit entry: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def get_audit_log(
        self,
        job_id: str,
        action_type: Optional[str] = None,
        user_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get audit log with filters
        
        Args:
            job_id: Job ID
            action_type: Filter by action type
            user_id: Filter by user
            date_from: Start date
            date_to: End date
            page: Page number
            limit: Items per page
        
        Returns:
            Paginated audit log entries
        """
        try:
            # Build query
            query = select(JobAuditLog).where(JobAuditLog.job_id == job_id)
            
            if action_type:
                query = query.where(JobAuditLog.action_type == action_type)
            
            if user_id:
                query = query.where(JobAuditLog.user_id == user_id)
            
            if date_from:
                query = query.where(JobAuditLog.timestamp >= datetime.fromisoformat(date_from))
            
            if date_to:
                query = query.where(JobAuditLog.timestamp <= datetime.fromisoformat(date_to))
            
            # Get total count
            count_result = await self.db.execute(
                select(func.count()).select_from(query.subquery())
            )
            total = count_result.scalar() or 0
            
            # Apply pagination
            offset = (page - 1) * limit
            query = query.order_by(JobAuditLog.timestamp.desc()).offset(offset).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            logs = result.scalars().all()
            
            # Format entries
            entries = []
            for log in logs:
                # Get user info
                user_result = await self.db.execute(
                    select(User).where(User.id == log.user_id)
                )
                user = user_result.scalar_one_or_none()
                
                entries.append({
                    "id": log.id,
                    "action_type": log.action_type,
                    "old_values": json.loads(log.old_values) if log.old_values else None,
                    "new_values": json.loads(log.new_values) if log.new_values else None,
                    "user": {
                        "id": user.id,
                        "name": user.full_name,
                        "email": user.email
                    } if user else None,
                    "timestamp": log.timestamp,
                    "ip_address": log.ip_address
                })
            
            return {
                "success": True,
                "audit_entries": entries,
                "pagination": {
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "total_pages": (total + limit - 1) // limit if total > 0 else 0
                }
            }
        
        except Exception as e:
            logger.error(f"Error fetching audit log: {str(e)}", exc_info=True)
            raise
    
    async def export_audit_log_csv(self, job_id: str) -> str:
        """
        Export audit log as CSV
        
        Args:
            job_id: Job ID
        
        Returns:
            CSV string
        """
        try:
            result = await self.db.execute(
                select(JobAuditLog)
                .where(JobAuditLog.job_id == job_id)
                .order_by(JobAuditLog.timestamp.desc())
            )
            logs = result.scalars().all()
            
            # Build CSV
            csv_lines = ["ID,Action Type,User,Timestamp,Old Values,New Values,IP Address"]
            
            for log in logs:
                # Get user
                user_result = await self.db.execute(
                    select(User).where(User.id == log.user_id)
                )
                user = user_result.scalar_one_or_none()
                user_name = user.full_name if user else "Unknown"
                
                csv_lines.append(
                    f"{log.id},{log.action_type},{user_name},{log.timestamp},"
                    f'"{log.old_values}","{log.new_values}",{log.ip_address or ""}'
                )
            
            return "\n".join(csv_lines)
        
        except Exception as e:
            logger.error(f"Error exporting audit log: {str(e)}", exc_info=True)
            raise
