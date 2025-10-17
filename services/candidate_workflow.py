"""
Candidate Workflow Service - Phase 3 Day 4
===========================================
Manages candidate status transitions and workflow validation.

Features:
- Status transition validation
- Automatic history tracking
- Workflow rules engine
- Status change notifications
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import (
    Candidate,
    CandidateStatusHistory,
    User
)
import uuid
import json

logger = logging.getLogger(__name__)


class CandidateWorkflowService:
    """Service for managing candidate workflow and status transitions"""
    
    # Valid status values
    VALID_STATUSES = {
        'new', 'screened', 'interviewed', 'offered', 'hired', 'rejected', 'archived'
    }
    
    # Valid status transitions (from_status -> allowed_to_statuses)
    VALID_TRANSITIONS = {
        'new': {'screened', 'rejected', 'archived'},
        'screened': {'interviewed', 'rejected', 'archived'},
        'interviewed': {'offered', 'rejected', 'archived', 'interviewed'},  # Can have multiple interview rounds
        'offered': {'hired', 'rejected', 'archived'},
        'hired': {'archived'},  # Can only archive hired candidates
        'rejected': {'archived', 'new'},  # Can reopen rejected candidates
        'archived': {'new'}  # Can unarchive
    }
    
    # Status descriptions
    STATUS_DESCRIPTIONS = {
        'new': 'Newly added candidate, pending initial review',
        'screened': 'Resume screened and passed initial evaluation',
        'interviewed': 'Candidate has been interviewed',
        'offered': 'Job offer extended to candidate',
        'hired': 'Candidate accepted offer and was hired',
        'rejected': 'Candidate rejected at some stage',
        'archived': 'Candidate archived (no longer active)'
    }
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def change_status(
        self,
        candidate_id: str,
        new_status: str,
        changed_by_user_id: str,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
        related_job_id: Optional[str] = None,
        related_interview_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CandidateStatusHistory:
        """
        Change candidate status with validation and history tracking.
        
        Args:
            candidate_id: Candidate ID
            new_status: New status to set
            changed_by_user_id: User making the change
            reason: Reason for status change
            notes: Additional notes
            related_job_id: Related job ID (if applicable)
            related_interview_id: Related interview ID (if applicable)
            metadata: Additional metadata
        
        Returns:
            CandidateStatusHistory record
        
        Raises:
            ValueError: If status transition is invalid
        """
        # Get candidate
        result = await self.session.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        candidate = result.scalar_one_or_none()
        
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")
        
        # Validate new status
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {self.VALID_STATUSES}")
        
        # Get current status
        current_status = candidate.status or 'new'
        
        # Check if status is actually changing
        if current_status == new_status:
            logger.warning(f"Status is already {new_status} for candidate {candidate_id}")
            # Still create history record for audit trail
        
        # Validate transition
        if not self._is_valid_transition(current_status, new_status):
            raise ValueError(
                f"Invalid status transition: {current_status} -> {new_status}. "
                f"Allowed transitions from {current_status}: {self.VALID_TRANSITIONS.get(current_status, set())}"
            )
        
        # Update candidate status
        old_status = candidate.status
        candidate.status = new_status
        
        # Create history record
        history = CandidateStatusHistory(
            id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            from_status=old_status,
            to_status=new_status,
            changed_by=changed_by_user_id,
            change_reason=reason,
            notes=notes,
            related_job_id=related_job_id,
            related_interview_id=related_interview_id,
            activity_metadata=json.dumps(metadata) if metadata else None
        )
        
        self.session.add(history)
        await self.session.commit()
        await self.session.refresh(history)
        
        logger.info(f"Changed candidate {candidate_id} status: {old_status} -> {new_status}")
        
        return history
    
    def _is_valid_transition(self, from_status: str, to_status: str) -> bool:
        """Check if status transition is valid"""
        if from_status == to_status:
            return True  # Allow same status (for audit trail)
        
        allowed_statuses = self.VALID_TRANSITIONS.get(from_status, set())
        return to_status in allowed_statuses
    
    async def get_status_history(
        self,
        candidate_id: str,
        limit: int = 50
    ) -> List[CandidateStatusHistory]:
        """
        Get status change history for a candidate.
        
        Args:
            candidate_id: Candidate ID
            limit: Maximum number of records to return
        
        Returns:
            List of status history records
        """
        result = await self.session.execute(
            select(CandidateStatusHistory)
            .where(CandidateStatusHistory.candidate_id == candidate_id)
            .order_by(CandidateStatusHistory.changed_at.desc())
            .limit(limit)
        )
        
        return result.scalars().all()
    
    async def get_candidates_by_status(
        self,
        status: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Candidate]:
        """
        Get candidates by status.
        
        Args:
            status: Status to filter by
            limit: Maximum number of candidates to return
            offset: Offset for pagination
        
        Returns:
            List of candidates
        """
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        
        result = await self.session.execute(
            select(Candidate)
            .where(Candidate.status == status)
            .where(Candidate.is_deleted == False)
            .order_by(Candidate.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        return result.scalars().all()
    
    async def get_workflow_statistics(self) -> Dict[str, Any]:
        """
        Get workflow statistics (candidates in each status).
        
        Returns:
            Dictionary with status counts
        """
        stats = {}
        
        for status in self.VALID_STATUSES:
            result = await self.session.execute(
                select(Candidate)
                .where(Candidate.status == status)
                .where(Candidate.is_deleted == False)
            )
            count = len(result.scalars().all())
            stats[status] = count
        
        # Calculate conversion rates
        total = sum(stats.values())
        if total > 0:
            stats['conversion_rates'] = {
                'screen_rate': (stats.get('screened', 0) / total) * 100 if total > 0 else 0,
                'interview_rate': (stats.get('interviewed', 0) / total) * 100 if total > 0 else 0,
                'offer_rate': (stats.get('offered', 0) / total) * 100 if total > 0 else 0,
                'hire_rate': (stats.get('hired', 0) / total) * 100 if total > 0 else 0,
            }
        
        stats['total'] = total
        
        return stats
    
    async def bulk_status_change(
        self,
        candidate_ids: List[str],
        new_status: str,
        changed_by_user_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Change status for multiple candidates.
        
        Args:
            candidate_ids: List of candidate IDs
            new_status: New status to set
            changed_by_user_id: User making the change
            reason: Reason for status change
        
        Returns:
            Dictionary with success/failure counts
        """
        results = {
            'total': len(candidate_ids),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for candidate_id in candidate_ids:
            try:
                await self.change_status(
                    candidate_id=candidate_id,
                    new_status=new_status,
                    changed_by_user_id=changed_by_user_id,
                    reason=reason
                )
                results['successful'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'candidate_id': candidate_id,
                    'error': str(e)
                })
                logger.error(f"Failed to change status for candidate {candidate_id}: {e}")
        
        return results
    
    def get_next_statuses(self, current_status: str) -> List[str]:
        """
        Get list of valid next statuses for current status.
        
        Args:
            current_status: Current candidate status
        
        Returns:
            List of valid next statuses
        """
        return list(self.VALID_TRANSITIONS.get(current_status, set()))
    
    def get_status_description(self, status: str) -> str:
        """Get human-readable description of status"""
        return self.STATUS_DESCRIPTIONS.get(status, 'Unknown status')
