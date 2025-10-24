"""Candidate Shortlist API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from typing import List
import logging

from core.database import get_db
from models.db.candidate import Candidate

logger = logging.getLogger(__name__)

router = APIRouter()

# Simple in-memory shortlist for MVP (can be replaced with database table later)
# Format: {user_id: [candidate_ids]}
shortlist_store = {}


@router.post("/candidates/{candidate_id}/shortlist")
async def add_to_shortlist(
    candidate_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Add candidate to shortlist"""
    try:
        # Verify candidate exists
        result = await db.execute(
            select(Candidate).where(Candidate.uuid == candidate_id)
        )
        candidate = result.scalar_one_or_none()
        
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # For now, use a global shortlist (in production, this would be per-user)
        user_id = "global"  # In production: get from session
        
        if user_id not in shortlist_store:
            shortlist_store[user_id] = []
        
        if candidate_id not in shortlist_store[user_id]:
            shortlist_store[user_id].append(candidate_id)
            logger.info(f"Added candidate {candidate_id} to shortlist")
        
        return {
            "success": True,
            "message": "Candidate added to shortlist",
            "shortlist_count": len(shortlist_store[user_id])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to shortlist: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/candidates/{candidate_id}/shortlist")
async def remove_from_shortlist(
    candidate_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove candidate from shortlist"""
    try:
        user_id = "global"  # In production: get from session
        
        if user_id in shortlist_store and candidate_id in shortlist_store[user_id]:
            shortlist_store[user_id].remove(candidate_id)
            logger.info(f"Removed candidate {candidate_id} from shortlist")
        
        return {
            "success": True,
            "message": "Candidate removed from shortlist",
            "shortlist_count": len(shortlist_store.get(user_id, []))
        }
        
    except Exception as e:
        logger.error(f"Error removing from shortlist: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candidates/{candidate_id}/shortlist/status")
async def check_shortlist_status(
    candidate_id: str
):
    """Check if candidate is in shortlist"""
    try:
        user_id = "global"  # In production: get from session
        is_shortlisted = candidate_id in shortlist_store.get(user_id, [])
        
        return {
            "is_shortlisted": is_shortlisted,
            "candidate_id": candidate_id
        }
        
    except Exception as e:
        logger.error(f"Error checking shortlist status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shortlist")
async def get_shortlist(
    db: AsyncSession = Depends(get_db)
):
    """Get all shortlisted candidates"""
    try:
        user_id = "global"  # In production: get from session
        candidate_ids = shortlist_store.get(user_id, [])
        
        if not candidate_ids:
            return {
                "candidates": [],
                "count": 0
            }
        
        # Fetch candidate details
        result = await db.execute(
            select(Candidate).where(Candidate.uuid.in_(candidate_ids))
        )
        candidates = result.scalars().all()
        
        return {
            "candidates": [
                {
                    "id": c.id,
                    "uuid": c.uuid,
                    "full_name": c.full_name,
                    "email": c.email,
                    "phone": c.phone,
                    "location": c.location,
                    "status": c.status
                }
                for c in candidates
            ],
            "count": len(candidates)
        }
        
    except Exception as e:
        logger.error(f"Error getting shortlist: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
