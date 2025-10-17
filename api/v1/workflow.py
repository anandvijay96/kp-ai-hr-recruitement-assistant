"""
Candidate Workflow API - Phase 3 Day 4
=======================================
API endpoints for candidate status management and workflow.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from core.database import get_db
from core.auth import get_current_user
from models.database import User
from services.candidate_workflow import CandidateWorkflowService

router = APIRouter()


# Request/Response Models
class StatusChangeRequest(BaseModel):
    new_status: str
    reason: Optional[str] = None
    notes: Optional[str] = None
    related_job_id: Optional[str] = None
    related_interview_id: Optional[str] = None


class BulkStatusChangeRequest(BaseModel):
    candidate_ids: List[str]
    new_status: str
    reason: Optional[str] = None


@router.post("/candidates/{candidate_id}/status")
async def change_candidate_status(
    candidate_id: str,
    request: StatusChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change candidate status with validation and history tracking.
    """
    workflow_service = CandidateWorkflowService(db)
    
    try:
        history = await workflow_service.change_status(
            candidate_id=candidate_id,
            new_status=request.new_status,
            changed_by_user_id=current_user.id,
            reason=request.reason,
            notes=request.notes,
            related_job_id=request.related_job_id,
            related_interview_id=request.related_interview_id
        )
        
        return {
            "success": True,
            "message": f"Status changed to {request.new_status}",
            "history_id": history.id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to change status: {str(e)}")


@router.get("/candidates/{candidate_id}/status-history")
async def get_candidate_status_history(
    candidate_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get status change history for a candidate.
    """
    workflow_service = CandidateWorkflowService(db)
    
    history = await workflow_service.get_status_history(candidate_id, limit=limit)
    
    return {
        "success": True,
        "data": [
            {
                "id": h.id,
                "from_status": h.from_status,
                "to_status": h.to_status,
                "changed_by": h.changed_by,
                "change_reason": h.change_reason,
                "notes": h.notes,
                "changed_at": h.changed_at.isoformat() if h.changed_at else None,
                "related_job_id": h.related_job_id,
                "related_interview_id": h.related_interview_id
            }
            for h in history
        ]
    }


@router.get("/workflow/statistics")
async def get_workflow_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get workflow statistics (candidates in each status).
    """
    workflow_service = CandidateWorkflowService(db)
    
    stats = await workflow_service.get_workflow_statistics()
    
    return {
        "success": True,
        "data": stats
    }


@router.get("/workflow/statuses")
async def get_valid_statuses(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of valid candidate statuses and their descriptions.
    """
    workflow_service = CandidateWorkflowService(None)  # No DB needed for this
    
    return {
        "success": True,
        "data": {
            "statuses": list(workflow_service.VALID_STATUSES),
            "descriptions": workflow_service.STATUS_DESCRIPTIONS,
            "transitions": workflow_service.VALID_TRANSITIONS
        }
    }


@router.get("/workflow/next-statuses/{current_status}")
async def get_next_statuses(
    current_status: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get valid next statuses for a given current status.
    """
    workflow_service = CandidateWorkflowService(None)
    
    next_statuses = workflow_service.get_next_statuses(current_status)
    
    return {
        "success": True,
        "data": {
            "current_status": current_status,
            "next_statuses": next_statuses,
            "descriptions": {
                status: workflow_service.get_status_description(status)
                for status in next_statuses
            }
        }
    }


@router.post("/workflow/bulk-status-change")
async def bulk_status_change(
    request: BulkStatusChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change status for multiple candidates at once (admin only).
    """
    # Check if user has permission (admin or manager)
    if current_user.role not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    workflow_service = CandidateWorkflowService(db)
    
    results = await workflow_service.bulk_status_change(
        candidate_ids=request.candidate_ids,
        new_status=request.new_status,
        changed_by_user_id=current_user.id,
        reason=request.reason
    )
    
    return {
        "success": True,
        "data": results
    }


@router.get("/candidates/by-status/{status}")
async def get_candidates_by_status(
    status: str,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get candidates filtered by status.
    """
    workflow_service = CandidateWorkflowService(db)
    
    try:
        candidates = await workflow_service.get_candidates_by_status(
            status=status,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "data": [
                {
                    "id": c.id,
                    "full_name": c.full_name,
                    "email": c.email,
                    "phone": c.phone,
                    "status": c.status,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None
                }
                for c in candidates
            ],
            "count": len(candidates)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
