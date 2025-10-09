"""API endpoints for candidate management"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
import logging

from models.candidate_schemas import (
    CandidateResponse, CandidateUpdate, PaginatedCandidateResponse,
    ResolveDuplicateRequest
)
from services.candidate_service import CandidateService
from core.dependencies import get_current_user
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/candidates", tags=["Candidates"])


def get_candidate_service(db: AsyncSession = Depends(get_db)) -> CandidateService:
    """Get candidate service instance"""
    return CandidateService(db_session=db)


# ============================================================================
# ENDPOINT 1: List Candidates (Paginated)
# ============================================================================

@router.get("", response_model=PaginatedCandidateResponse)
async def list_candidates(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service)
):
    """
    Get paginated list of candidates
    
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    - **search**: Search term for name, email, or phone
    - **status**: Filter by candidate status
    
    Returns paginated list of candidates with summary information
    """
    try:
        result = await candidate_service.search_candidates(
            search=search,
            status=status,
            page=page,
            limit=limit
        )
        
        return PaginatedCandidateResponse(
            success=True,
            data=result
        )
    
    except Exception as e:
        logger.error(f"Error listing candidates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve candidates"
        )


# ============================================================================
# ENDPOINT 2: Get Candidate Details
# ============================================================================

@router.get("/{candidate_id}", response_model=dict)
async def get_candidate(
    candidate_id: str,
    current_user: dict = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service)
):
    """
    Get detailed information about a candidate
    
    - **candidate_id**: Candidate UUID
    
    Returns complete candidate profile with education, experience, skills, and certifications
    """
    try:
        logger.info(f"Fetching candidate {candidate_id} for user {current_user.get('id')}")
        
        candidate = await candidate_service.get_candidate_by_id(
            candidate_id=candidate_id,
            include_relations=True
        )
        
        if not candidate:
            logger.warning(f"Candidate {candidate_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        logger.info(f"Successfully retrieved candidate {candidate_id}")
        return {
            "success": True,
            "data": candidate
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidate {candidate_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve candidate details: {str(e)}"
        )


# ============================================================================
# ENDPOINT 3: Update Candidate
# ============================================================================

@router.put("/{candidate_id}", response_model=dict)
async def update_candidate(
    candidate_id: str,
    update_data: CandidateUpdate,
    current_user: dict = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service)
):
    """
    Update candidate information
    
    - **candidate_id**: Candidate UUID
    - **update_data**: Fields to update
    
    Only admins or the user who created the candidate can update
    """
    try:
        # Check if candidate exists
        existing = await candidate_service.get_candidate_by_id(
            candidate_id=candidate_id,
            include_relations=False
        )
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        # Update candidate
        updated_candidate = await candidate_service.update_candidate(
            candidate_id=candidate_id,
            update_data=update_data
        )
        
        return {
            "success": True,
            "message": "Candidate updated successfully",
            "data": updated_candidate
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating candidate {candidate_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update candidate"
        )


# ============================================================================
# ENDPOINT 4: Delete Candidate
# ============================================================================

@router.delete("/{candidate_id}")
async def delete_candidate(
    candidate_id: str,
    current_user: dict = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service)
):
    """
    Delete a candidate (soft delete by archiving)
    
    - **candidate_id**: Candidate UUID
    
    Only admins can delete candidates
    """
    try:
        # Check admin role
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can delete candidates"
            )
        
        success = await candidate_service.delete_candidate(
            candidate_id=candidate_id,
            deleted_by=current_user["id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        return {
            "success": True,
            "message": "Candidate deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting candidate {candidate_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete candidate"
        )


# ============================================================================
# ENDPOINT 5: Merge Candidates
# ============================================================================

@router.post("/{source_id}/merge/{target_id}")
async def merge_candidates(
    source_id: str,
    target_id: str,
    current_user: dict = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service)
):
    """
    Merge two candidate records
    
    - **source_id**: Source candidate ID (will be archived)
    - **target_id**: Target candidate ID (will be kept)
    
    All data from source will be moved to target
    """
    try:
        # Check admin role
        if current_user.get("role") not in ["admin", "manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and managers can merge candidates"
            )
        
        result_id = await candidate_service.merge_candidates(
            source_id=source_id,
            target_id=target_id,
            merged_by=current_user["id"]
        )
        
        return {
            "success": True,
            "message": "Candidates merged successfully",
            "data": {
                "merged_candidate_id": result_id
            }
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error merging candidates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to merge candidates"
        )


# ============================================================================
# ENDPOINT 6: Debug - Get Candidate Raw Data
# ============================================================================

@router.get("/{candidate_id}/debug")
async def debug_candidate(
    candidate_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Debug endpoint to check raw candidate data"""
    try:
        from sqlalchemy import select
        from models.database import Candidate
        
        result = await db.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        candidate = result.scalar_one_or_none()
        
        if not candidate:
            return {"found": False, "candidate_id": candidate_id}
        
        return {
            "found": True,
            "id": candidate.id,
            "full_name": candidate.full_name,
            "email": candidate.email,
            "status": candidate.status
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# ENDPOINT 7: Get Candidate Statistics
# ============================================================================

@router.get("/stats/overview")
async def get_candidate_statistics(
    current_user: dict = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service)
):
    """
    Get candidate statistics overview
    
    Returns counts by status, source, and other metrics
    """
    try:
        from sqlalchemy import select, func
        from models.database import Candidate
        
        db = candidate_service.db
        
        # Total candidates
        total_result = await db.execute(
            select(func.count()).select_from(Candidate)
        )
        total = total_result.scalar()
        
        # By status
        status_result = await db.execute(
            select(Candidate.status, func.count())
            .group_by(Candidate.status)
        )
        by_status = {row[0]: row[1] for row in status_result.all()}
        
        # By source
        source_result = await db.execute(
            select(Candidate.source, func.count())
            .group_by(Candidate.source)
        )
        by_source = {row[0]: row[1] for row in source_result.all()}
        
        return {
            "success": True,
            "data": {
                "total_candidates": total,
                "by_status": by_status,
                "by_source": by_source
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting candidate statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )
