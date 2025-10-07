from fastapi import APIRouter, Depends, Body
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from core.database import get_db
from services.filter_service import FilterService
from services.preset_service import PresetService
from services.candidate_service import CandidateService
from models.filter_models import CandidateFilter, FilterPresetCreate, FilterPresetResponse

router = APIRouter()
filter_service = FilterService()
preset_service = PresetService()
candidate_service = CandidateService()

@router.post("/search")
def search_candidates(filters: CandidateFilter, page: int = 1, page_size: int = 20, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Searches and filters candidates using database queries."""
    return filter_service.search_candidates(filters, db, page, page_size)

@router.get("/filter-options")
def get_filter_options(db: Session = Depends(get_db)) -> Dict[str, List]:
    """Retrieves available options for filters from the database."""
    return filter_service.get_filter_options(db)

@router.post("/filter-presets", response_model=FilterPresetResponse)
def create_filter_preset(preset_data: FilterPresetCreate, user_id: int = 1) -> FilterPresetResponse: # Assuming user_id=1 for demo
    """Saves a new filter preset."""
    return preset_service.create_preset(user_id, preset_data)

@router.get("/filter-presets", response_model=List[FilterPresetResponse])
def get_filter_presets(user_id: int = 1) -> List[FilterPresetResponse]: # Assuming user_id=1 for demo
    """Retrieves all saved filter presets for the user."""
    return preset_service.get_presets_for_user(user_id)

@router.get("/")
def get_all_candidates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all candidates with pagination."""
    candidates = candidate_service.get_all_candidates(db, skip, limit)
    return {"candidates": candidates, "total": len(candidates)}

@router.get("/{candidate_id}")
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Get candidate by ID with all related data."""
    candidate = candidate_service.get_candidate_by_id(candidate_id, db)
    if not candidate:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

@router.post("/check-duplicate")
def check_duplicate_candidate(
    email: Optional[str] = Body(None),
    phone: Optional[str] = Body(None),
    name: Optional[str] = Body(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check if candidate already exists in the database.
    Returns duplicate detection results with confidence scores.
    """
    if not email and not phone and not name:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400, 
            detail="At least one of email, phone, or name must be provided"
        )
    
    return candidate_service.check_duplicate(email, phone, name, db)
