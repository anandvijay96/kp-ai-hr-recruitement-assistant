"""
API endpoints for candidate ratings
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from core.database import get_db
from models.database import CandidateRating, Candidate, User

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic models for request/response
class RatingCreate(BaseModel):
    """Request model for creating a rating"""
    candidate_id: str
    technical_skills: Optional[int] = Field(None, ge=1, le=5)
    communication: Optional[int] = Field(None, ge=1, le=5)
    culture_fit: Optional[int] = Field(None, ge=1, le=5)
    experience_level: Optional[int] = Field(None, ge=1, le=5)
    overall_rating: Optional[int] = Field(None, ge=1, le=5)
    comments: Optional[str] = None
    strengths: Optional[str] = None
    concerns: Optional[str] = None
    recommendation: Optional[str] = Field(None, pattern="^(highly_recommended|recommended|maybe|not_recommended)$")


class RatingUpdate(BaseModel):
    """Request model for updating a rating"""
    technical_skills: Optional[int] = Field(None, ge=1, le=5)
    communication: Optional[int] = Field(None, ge=1, le=5)
    culture_fit: Optional[int] = Field(None, ge=1, le=5)
    experience_level: Optional[int] = Field(None, ge=1, le=5)
    overall_rating: Optional[int] = Field(None, ge=1, le=5)
    comments: Optional[str] = None
    strengths: Optional[str] = None
    concerns: Optional[str] = None
    recommendation: Optional[str] = Field(None, pattern="^(highly_recommended|recommended|maybe|not_recommended)$")


class RatingResponse(BaseModel):
    """Response model for rating"""
    id: str
    candidate_id: str
    user_id: Optional[str]
    user_name: Optional[str]
    technical_skills: Optional[int]
    communication: Optional[int]
    culture_fit: Optional[int]
    experience_level: Optional[int]
    overall_rating: Optional[int]
    comments: Optional[str]
    strengths: Optional[str]
    concerns: Optional[str]
    recommendation: Optional[str]
    created_at: str
    updated_at: str


@router.post("/candidates/{candidate_id}/rate")
async def create_rating(
    candidate_id: str,
    rating_data: RatingCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new rating for a candidate"""
    try:
        # Get current user from session
        user_email = request.session.get("user_email")
        if not user_email:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get user
        stmt = select(User).filter(User.email == user_email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify candidate exists
        stmt = select(Candidate).filter(Candidate.id == candidate_id)
        result = await db.execute(stmt)
        candidate = result.scalar_one_or_none()
        
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Calculate overall rating if not provided
        overall = rating_data.overall_rating
        if not overall:
            ratings = [r for r in [
                rating_data.technical_skills,
                rating_data.communication,
                rating_data.culture_fit,
                rating_data.experience_level
            ] if r is not None]
            
            if ratings:
                overall = round(sum(ratings) / len(ratings))
        
        # Create rating
        rating = CandidateRating(
            candidate_id=candidate_id,
            user_id=user.id,
            technical_skills=rating_data.technical_skills,
            communication=rating_data.communication,
            culture_fit=rating_data.culture_fit,
            experience_level=rating_data.experience_level,
            overall_rating=overall,
            comments=rating_data.comments,
            strengths=rating_data.strengths,
            concerns=rating_data.concerns,
            recommendation=rating_data.recommendation
        )
        
        db.add(rating)
        await db.commit()
        await db.refresh(rating)
        
        logger.info(f"Rating created for candidate {candidate_id} by user {user.email}")
        
        return {
            "id": rating.id,
            "candidate_id": rating.candidate_id,
            "overall_rating": rating.overall_rating,
            "message": "Rating created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating rating: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candidates/{candidate_id}/ratings")
async def get_candidate_ratings(
    candidate_id: str,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all ratings for a candidate"""
    try:
        # Get ratings with user info
        stmt = select(CandidateRating, User).join(
            User, CandidateRating.user_id == User.id, isouter=True
        ).filter(
            CandidateRating.candidate_id == candidate_id
        ).order_by(desc(CandidateRating.created_at))
        
        result = await db.execute(stmt)
        ratings_with_users = result.all()
        
        return [{
            "id": rating.id,
            "candidate_id": rating.candidate_id,
            "user_id": rating.user_id,
            "user_name": user.full_name if user else "Unknown",
            "technical_skills": rating.technical_skills,
            "communication": rating.communication,
            "culture_fit": rating.culture_fit,
            "experience_level": rating.experience_level,
            "overall_rating": rating.overall_rating,
            "comments": rating.comments,
            "strengths": rating.strengths,
            "concerns": rating.concerns,
            "recommendation": rating.recommendation,
            "created_at": rating.created_at.isoformat() if rating.created_at else None,
            "updated_at": rating.updated_at.isoformat() if rating.updated_at else None
        } for rating, user in ratings_with_users]
        
    except Exception as e:
        logger.error(f"Error getting ratings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candidates/{candidate_id}/rating-summary")
async def get_rating_summary(
    candidate_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get rating summary for a candidate (averages, count, etc.)"""
    try:
        # Get all ratings for candidate
        stmt = select(CandidateRating).filter(
            CandidateRating.candidate_id == candidate_id
        )
        result = await db.execute(stmt)
        ratings = result.scalars().all()
        
        if not ratings:
            return {
                "candidate_id": candidate_id,
                "total_ratings": 0,
                "average_overall": None,
                "average_technical": None,
                "average_communication": None,
                "average_culture_fit": None,
                "average_experience": None,
                "recommendation_breakdown": {}
            }
        
        # Calculate averages
        def avg(values):
            valid = [v for v in values if v is not None]
            return round(sum(valid) / len(valid), 1) if valid else None
        
        # Recommendation breakdown
        rec_breakdown = {}
        for rating in ratings:
            if rating.recommendation:
                rec_breakdown[rating.recommendation] = rec_breakdown.get(rating.recommendation, 0) + 1
        
        return {
            "candidate_id": candidate_id,
            "total_ratings": len(ratings),
            "average_overall": avg([r.overall_rating for r in ratings]),
            "average_technical": avg([r.technical_skills for r in ratings]),
            "average_communication": avg([r.communication for r in ratings]),
            "average_culture_fit": avg([r.culture_fit for r in ratings]),
            "average_experience": avg([r.experience_level for r in ratings]),
            "recommendation_breakdown": rec_breakdown,
            "latest_rating_date": max([r.created_at for r in ratings]).isoformat() if ratings else None
        }
        
    except Exception as e:
        logger.error(f"Error getting rating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/ratings/{rating_id}")
async def update_rating(
    rating_id: str,
    rating_data: RatingUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update an existing rating"""
    try:
        # Get current user
        user_email = request.session.get("user_email")
        if not user_email:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get rating
        stmt = select(CandidateRating).filter(CandidateRating.id == rating_id)
        result = await db.execute(stmt)
        rating = result.scalar_one_or_none()
        
        if not rating:
            raise HTTPException(status_code=404, detail="Rating not found")
        
        # Get user
        stmt = select(User).filter(User.email == user_email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        # Check if user owns this rating or is admin
        if rating.user_id != user.id and user.role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to update this rating")
        
        # Update fields
        if rating_data.technical_skills is not None:
            rating.technical_skills = rating_data.technical_skills
        if rating_data.communication is not None:
            rating.communication = rating_data.communication
        if rating_data.culture_fit is not None:
            rating.culture_fit = rating_data.culture_fit
        if rating_data.experience_level is not None:
            rating.experience_level = rating_data.experience_level
        if rating_data.overall_rating is not None:
            rating.overall_rating = rating_data.overall_rating
        if rating_data.comments is not None:
            rating.comments = rating_data.comments
        if rating_data.strengths is not None:
            rating.strengths = rating_data.strengths
        if rating_data.concerns is not None:
            rating.concerns = rating_data.concerns
        if rating_data.recommendation is not None:
            rating.recommendation = rating_data.recommendation
        
        # Recalculate overall if not explicitly set
        if rating_data.overall_rating is None:
            ratings = [r for r in [
                rating.technical_skills,
                rating.communication,
                rating.culture_fit,
                rating.experience_level
            ] if r is not None]
            
            if ratings:
                rating.overall_rating = round(sum(ratings) / len(ratings))
        
        await db.commit()
        await db.refresh(rating)
        
        logger.info(f"Rating {rating_id} updated by user {user.email}")
        
        return {
            "id": rating.id,
            "message": "Rating updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating rating: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/ratings/{rating_id}")
async def delete_rating(
    rating_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete a rating"""
    try:
        # Get current user
        user_email = request.session.get("user_email")
        if not user_email:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get rating
        stmt = select(CandidateRating).filter(CandidateRating.id == rating_id)
        result = await db.execute(stmt)
        rating = result.scalar_one_or_none()
        
        if not rating:
            raise HTTPException(status_code=404, detail="Rating not found")
        
        # Get user
        stmt = select(User).filter(User.email == user_email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        # Check if user owns this rating or is admin
        if rating.user_id != user.id and user.role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to delete this rating")
        
        await db.delete(rating)
        await db.commit()
        
        logger.info(f"Rating {rating_id} deleted by user {user.email}")
        
        return {"message": "Rating deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting rating: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
